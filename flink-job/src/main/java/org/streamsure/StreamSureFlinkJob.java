package org.streamsure;

import org.apache.flink.shaded.jackson2.com.fasterxml.jackson.databind.JsonNode;
import org.apache.flink.shaded.jackson2.com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.flink.shaded.jackson2.com.fasterxml.jackson.databind.node.ArrayNode;
import org.apache.flink.shaded.jackson2.com.fasterxml.jackson.databind.node.ObjectNode;
import org.apache.flink.api.common.eventtime.WatermarkStrategy;
import org.apache.flink.api.common.serialization.SimpleStringSchema;
import org.apache.flink.api.common.state.MapState;
import org.apache.flink.api.common.state.MapStateDescriptor;
import org.apache.flink.api.common.state.ValueState;
import org.apache.flink.api.common.state.ValueStateDescriptor;
import org.apache.flink.api.java.utils.ParameterTool;
import org.apache.flink.connector.kafka.sink.KafkaRecordSerializationSchema;
import org.apache.flink.connector.kafka.sink.KafkaSink;
import org.apache.flink.connector.kafka.source.KafkaSource;
import org.apache.flink.streaming.api.datastream.DataStream;
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;
import org.apache.flink.streaming.api.functions.KeyedProcessFunction;
import org.apache.flink.util.Collector;

import java.util.*;

public class StreamSureFlinkJob {
  public static void main(String[] args) throws Exception {
    ParameterTool p = ParameterTool.fromArgs(args);
    String bootstrap = p.get("bootstrap", "kafka:9092");
    String inTopic = p.get("input-topic", "streamsure.events");
    String outTopic = p.get("output-topic", "streamsure.certify.requests");
    String group = p.get("group", "streamsure-flink-v130");
    int parallelism = p.getInt("parallelism", 1);

    StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
    env.enableCheckpointing(5000);
    env.setParallelism(parallelism);

    KafkaSource<String> source = KafkaSource.<String>builder()
        .setBootstrapServers(bootstrap).setTopics(inTopic).setGroupId(group)
        .setValueOnlyDeserializer(new SimpleStringSchema()).setStartingOffsets(org.apache.flink.connector.kafka.source.enumerator.initializer.OffsetsInitializer.earliest())
        .build();
    KafkaSink<String> sink = KafkaSink.<String>builder().setBootstrapServers(bootstrap)
        .setRecordSerializer(KafkaRecordSerializationSchema.builder().setTopic(outTopic).setValueSerializationSchema(new SimpleStringSchema()).build())
        .build();

    DataStream<String> requests = env.fromSource(source, WatermarkStrategy.noWatermarks(), "streamsure-kafka-source")
        .keyBy(StreamSureFlinkJob::keyOf)
        .process(new InventoryAssembler());
    requests.sinkTo(sink).name("streamsure-certify-request-sink");
    env.execute("STREAM-SURE Decision-Bearing State Derivation");
  }

  static String keyOf(String s) {
    try { return new ObjectMapper().readTree(s).path("state_id").asText("unknown"); }
    catch (Exception e) { return "malformed"; }
  }

  public static class InventoryAssembler extends KeyedProcessFunction<String,String,String> {
    private transient MapState<String,Double> available;
    private transient MapState<String,Long> eventTimes;
    private transient MapState<String,Boolean> semanticOk;
    private transient ValueState<Integer> version;
    private final ObjectMapper om = new ObjectMapper();

    @Override public void open(org.apache.flink.configuration.Configuration c) {
      available=getRuntimeContext().getMapState(new MapStateDescriptor<>("available",String.class,Double.class));
      eventTimes=getRuntimeContext().getMapState(new MapStateDescriptor<>("eventTimes",String.class,Long.class));
      semanticOk=getRuntimeContext().getMapState(new MapStateDescriptor<>("semanticOk",String.class,Boolean.class));
      version=getRuntimeContext().getState(new ValueStateDescriptor<>("version",Integer.class));
    }

    @Override public void processElement(String raw, Context ctx, Collector<String> out) throws Exception {
      JsonNode e=om.readTree(raw); String type=e.path("type").asText();
      if ("warehouse_update".equals(type)) {
        String source=e.path("source").asText();
        available.put(source,e.path("available").asDouble());
        eventTimes.put(source,e.path("event_time_ms").asLong(System.currentTimeMillis()));
        semanticOk.put(source,e.path("semantic_ok").asBoolean(true));
        Integer v=version.value(); version.update(v==null?1:v+1); return;
      }
      if (!"decision".equals(type)) return;

      List<String> reqSources=new ArrayList<>(); e.path("required_sources").forEach(x->reqSources.add(x.asText()));
      long decisionTime=e.path("event_time_ms").asLong(System.currentTimeMillis());
      long maxAge=e.path("max_age_ms").asLong(5000);
      double total=0; boolean allPresent=true; boolean anyStale=false; boolean contractsOk=true;
      ObjectNode completeness=om.createObjectNode(), freshness=om.createObjectNode();
      for (String s:reqSources) {
        Double a=available.get(s); Long ts=eventTimes.get(s); Boolean sem=semanticOk.get(s);
        boolean present=a!=null; completeness.put(s,present); if(!present) allPresent=false;
        if(a!=null) total+=a;
        double age=ts==null?999999.0:Math.max(0,decisionTime-ts)/1000.0; freshness.put(s,age);
        if(ts!=null && decisionTime-ts>maxAge) anyStale=true;
        if(Boolean.FALSE.equals(sem)) contractsOk=false;
      }
      String freshState = !allPresent ? "UNKNOWN" : (anyStale?"FAIL":"PASS");
      String contractState = contractsOk?"PASS":"FAIL";
      ObjectNode payload=om.createObjectNode(), state=payload.putObject("state"), decision=payload.putObject("decision");
      state.put("state_id",e.path("state_id").asText()); state.put("state_version",Optional.ofNullable(version.value()).orElse(1)); state.put("domain","inventory");
      ObjectNode value=state.putObject("value"); value.put("committed_inventory",e.path("committed_inventory").asDouble()); value.put("verified_available_inventory",total);
      ObjectNode ev=state.putObject("evidence"); ev.put("temporal","PASS"); ev.put("contract",contractState); ev.put("lineage","PASS"); ev.put("freshness",freshState); ev.put("uncertainty","PASS"); ev.put("invariant","PASS"); ev.put("decision_policy","PASS");
      ObjectNode details=ev.putObject("details"); details.put("derived_by","apache-flink"); details.put("source_count",reqSources.size());
      state.put("event_time_start",decisionTime/1000.0-1); state.put("event_time_end",decisionTime/1000.0);
      ArrayNode rs=state.putArray("required_sources"); reqSources.forEach(rs::add); state.set("source_freshness",freshness); state.set("source_completeness",completeness);
      ObjectNode cv=state.putObject("contract_versions"); cv.put("inventory","1.0"); ObjectNode pv=state.putObject("producer_versions"); reqSources.forEach(x->pv.put(x,"1.0"));
      state.put("transformation_version","flink-1.3.1");
      if (e.has("sent_at_ns")) details.put("sent_at_ns", e.path("sent_at_ns").asLong());
      if (e.has("run_id")) details.put("run_id", e.path("run_id").asText()); state.put("lineage_reference","flink://"+e.path("state_id").asText()); state.putObject("uncertainty_context").put("score",0.05);
      decision.put("decision_id",e.path("decision_id").asText()); decision.put("decision_class",e.path("decision_class").asInt()); decision.put("purpose",e.path("purpose").asText("distributed-smoke"));
      out.collect(om.writeValueAsString(payload));
    }
  }
}
