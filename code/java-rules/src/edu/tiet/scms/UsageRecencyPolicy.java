package edu.tiet.scms;
import java.util.*;
public final class UsageRecencyPolicy implements AllocationPolicy {
    public List<Score> rank(List<Candidate> input, double threshold, double weight) {
        int max=input.stream().mapToInt(Candidate::sessions).max().orElse(0);
        record Ranked(Candidate candidate, double score) {}
        List<Ranked> ranks=new ArrayList<>();
        for (Candidate c:input) {
            double penalty=c.daysSince()<threshold
                ? Math.max(0.0,(threshold-c.daysSince())*weight):0.0;
            ranks.add(new Ranked(c,c.sessions()/(double)Math.max(max,1)+penalty));
        }
        ranks.sort(Comparator.comparingDouble(Ranked::score)
            .thenComparing(r->r.candidate().createdAt()));
        return ranks.stream().map(r->new Score(r.candidate().id(),r.score())).toList();
    }
}
