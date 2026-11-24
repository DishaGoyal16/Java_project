package edu.tiet.scms;
import com.sun.net.httpserver.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.*;
import java.util.concurrent.*;
/** Loopback-only authenticated internal HTTP adapter; never expose to clients. */
public final class RulesServer {
    private final WorkflowRules workflows=new WorkflowRules();
    private final AllocationPolicy allocation=new UsageRecencyPolicy();
    private final String token;
    private RulesServer(String token) {this.token=token;}
    static String quote(String s) {
        StringBuilder b=new StringBuilder("\"");
        for(char c:s.toCharArray()) {
            if(c=='"'||c=='\\') b.append('\\').append(c);
            else if(c<32) b.append(String.format("\\u%04x",(int)c));
            else b.append(c);
        }
        return b.append('"').toString();
    }
    private void handle(HttpExchange e) throws java.io.IOException {
        int status=200;String response;
        try {
            String auth=e.getRequestHeaders().getFirst("Authorization");
            if(auth==null||!MessageDigest.isEqual(auth.getBytes(StandardCharsets.UTF_8),("Bearer "+token).getBytes(StandardCharsets.UTF_8)))
                throw new RuleViolation(401,"UNAUTHORIZED","Internal authentication required.");
            String path=e.getRequestURI().getPath();
            if(path.equals("/internal/health")&&e.getRequestMethod().equals("GET")) response="{\"status\":\"ok\"}";
            else {
                if(!e.getRequestMethod().equals("POST")) throw new RuleViolation(405,"METHOD_NOT_ALLOWED","POST required.");
                if(!path.startsWith("/internal/")) throw new RuleViolation(404,"NOT_FOUND","Not found.");
                byte[] bytes=e.getRequestBody().readNBytes(1048577);
                if(bytes.length>1048576) throw new RuleViolation(413,"TOO_LARGE","Request too large.");
                Map<String,String> p=new HashMap<>();
                for(String item:new String(bytes,StandardCharsets.UTF_8).split("&")) {
                    String[] kv=item.split("=",2);
                    if(kv.length==2)p.put(URLDecoder.decode(kv[0],StandardCharsets.UTF_8),URLDecoder.decode(kv[1],StandardCharsets.UTF_8));
                }
                String op=path.substring("/internal/".length());
                if(op.equals("rank")) {
                    int count=Integer.parseInt(p.get("count"));
                    if(count<0||count>10000)throw new IllegalArgumentException();
                    List<AllocationPolicy.Candidate> candidates=new ArrayList<>();
                    for(int i=0;i<count;i++) {
                        String k="c"+i+"_";
                        double days=Double.parseDouble(p.get(k+"days"));
                        if(!Double.isFinite(days))throw new IllegalArgumentException();
                        candidates.add(new AllocationPolicy.Candidate(Long.parseLong(p.get(k+"id")),Integer.parseInt(p.get(k+"sessions")),days,Instant.parse(p.get(k+"created"))));
                    }
                    double threshold=Double.parseDouble(p.get("threshold")),weight=Double.parseDouble(p.get("weight"));
                    if(!Double.isFinite(threshold)||!Double.isFinite(weight))throw new IllegalArgumentException();
                    StringJoiner out=new StringJoiner(",","[","]");
                    for(var s:allocation.rank(candidates,threshold,weight))out.add("{\"id\":"+s.id()+",\"score\":"+s.score()+"}");
                    response=out.toString();
                } else {workflows.validate(op,p);response="{\"success\":true}";}
            }
        } catch(RuleViolation ex) {
            status=ex.status;response="{\"success\":false,\"error\":{\"code\":"+quote(ex.code)+",\"message\":"+quote(ex.getMessage())+"}}";
        } catch(IllegalArgumentException|NullPointerException ex) {
            status=400;response="{\"success\":false,\"error\":{\"code\":\"INVALID_RULE_INPUT\",\"message\":\"Invalid internal request.\"}}";
        }
        if("true".equalsIgnoreCase(System.getenv("SCMS_RULES_DIAGNOSTICS"))) {
            String operation=e.getRequestURI().getPath().replace("/internal/", "");
            if(!Set.of("rank","booking","cancel","issue","return","health").contains(operation))operation="unknown";
            String handler=operation.equals("rank")?"UsageRecencyPolicy.rank":"WorkflowRules.validate";
            if(operation.equals("health"))handler="RulesServer.handle";
            System.out.printf("SCMS engine=java operation=%s handler=%s status=%d fallback=false%n",operation,handler,status);
        }
        byte[] out=response.getBytes(StandardCharsets.UTF_8);e.getResponseHeaders().set("Content-Type","application/json; charset=utf-8");
        e.sendResponseHeaders(status,out.length);try(var stream=e.getResponseBody()){stream.write(out);}finally{e.close();}
    }
    public static void main(String[] args) throws Exception {
        String token=System.getenv("SCMS_RULES_TOKEN");
        if(token==null||token.length()<32)throw new IllegalArgumentException("SCMS_RULES_TOKEN must have at least 32 characters");
        int port=Integer.parseInt(System.getenv().getOrDefault("SCMS_RULES_PORT","8091"));
        var server=HttpServer.create(new InetSocketAddress("127.0.0.1",port),128);
        server.createContext("/",new RulesServer(token)::handle);
        var pool=new ThreadPoolExecutor(4,16,30,TimeUnit.SECONDS,new ArrayBlockingQueue<>(128),new ThreadPoolExecutor.CallerRunsPolicy());
        server.setExecutor(pool);
        Runtime.getRuntime().addShutdownHook(new Thread(()->{server.stop(1);pool.shutdown();}));
        server.start();System.out.println("SCMS Java rules listening on loopback port "+port);
    }
}
