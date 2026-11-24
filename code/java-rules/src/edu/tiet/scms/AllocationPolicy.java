package edu.tiet.scms;
import java.time.Instant;
import java.util.List;
public interface AllocationPolicy {
    record Candidate(long id, int sessions, double daysSince, Instant createdAt) {}
    record Score(long id, double score) {}
    List<Score> rank(List<Candidate> candidates, double threshold, double weight);
}
