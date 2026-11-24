package edu.tiet.scms;
import java.util.Map;
import java.util.Set;
/** Pure domain decisions. Persistence and authenticated identity stay in the API adapter. */
public final class WorkflowRules {
    private static void require(boolean condition,int status,String code,String message) {
        if(!condition) throw new RuleViolation(status,code,message);
    }
    public void validate(String operation,Map<String,String> p) {
        switch(operation) {
            case "booking" -> {
                require(!"SUSPENDED".equals(p.get("student_status")),403,"ACCOUNT_SUSPENDED","Account is suspended.");
                require(!"true".equals(p.get("defaulter")),403,"ACTIVE_DEFAULTER","You have an overdue equipment item. Please return it before making new bookings.");
                require("true".equals(p.get("slot_exists")),404,"SLOT_NOT_FOUND","Slot not found.");
                require("OPEN".equals(p.get("slot_status")),400,"SLOT_NOT_AVAILABLE","Slot is not open for booking.");
                require(!"true".equals(p.get("cutoff_reached")),400,"SLOT_BOOKING_CLOSED","Booking window for this slot has closed.");
                require(Integer.parseInt(p.get("capacity"))!=0,400,"SLOT_NOT_AVAILABLE","Slot has zero capacity.");
                require(!"true".equals(p.get("duplicate")),409,"DUPLICATE_BOOKING","You already have a booking for this slot.");
                int cap=Integer.parseInt(p.get("daily_cap"));
                require(Integer.parseInt(p.get("sessions_today"))<cap,400,"USAGE_CAP_REACHED","Daily usage cap of "+cap+" sessions reached.");
            }
            case "cancel" -> {
                require("true".equals(p.get("owned")),404,"BOOKING_NOT_FOUND","Booking not found.");
                require(Set.of("REQUESTED","CONFIRMED","WAITLISTED").contains(p.get("status")),400,"BOOKING_CANNOT_CANCEL","This booking cannot be cancelled.");
            }
            case "issue" -> {
                require("true".equals(p.get("booking_exists")),404,"BOOKING_NOT_FOUND","Booking not found.");
                require("CONFIRMED".equals(p.get("booking_status")),400,"BOOKING_NOT_CONFIRMED","Only CONFIRMED bookings can be issued.");
                require("true".equals(p.get("equipment_exists")),404,"EQUIPMENT_NOT_FOUND","Equipment not found.");
                require("true".equals(p.get("matches")),400,"EQUIPMENT_MISMATCH","Scanned equipment does not match the booking.");
                require("AVAILABLE".equals(p.get("equipment_status")),400,"EQUIPMENT_ALREADY_ISSUED","Equipment is not available.");
            }
            case "return" -> {
                require("true".equals(p.get("transaction_exists")),404,"TRANSACTION_NOT_FOUND","Transaction not found.");
                require(Set.of("ISSUED","OVERDUE").contains(p.get("status")),400,"INVALID_TRANSACTION_STATE","Transaction is not in a returnable state.");
                require(!"DAMAGED".equals(p.get("condition"))||"true".equals(p.get("has_report")),400,"DAMAGE_REPORT_REQUIRED","A damage report is required for DAMAGED condition.");
            }
            default -> throw new IllegalArgumentException("Unknown operation");
        }
    }
}
