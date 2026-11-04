package com.example.payment.controller;

import com.example.payment.dto.PaymentRequest;
import com.example.payment.dto.PaymentResponse;
import com.example.payment.service.PaymentService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/payments")
public class PaymentController {

    // Issue: Field injection anti-pattern instead of constructor injection
    @Autowired
    private PaymentService paymentService;

    // Issue: Missing @Valid annotation on @RequestBody DTO
    @PostMapping("/charge")
    public ResponseEntity<PaymentResponse> processCharge(@RequestBody PaymentRequest request) {
        PaymentResponse response = paymentService.executePayment(request);
        // Issue: Returning 200 OK for resource creation instead of 201 Created
        return ResponseEntity.ok(response);
    }

    @GetMapping("/{id}")
    public ResponseEntity<PaymentResponse> getPayment(@PathVariable String id) {
        return ResponseEntity.ok(paymentService.getPaymentById(id));
    }
}
