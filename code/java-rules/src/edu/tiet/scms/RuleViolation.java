package edu.tiet.scms;
public final class RuleViolation extends RuntimeException {
    public final int status;
    public final String code;
    public RuleViolation(int status, String code, String message) {
        super(message); this.status=status; this.code=code;
    }
}
