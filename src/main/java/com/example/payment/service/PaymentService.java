package com.example.payment.service;

import com.example.payment.dto.PaymentRequest;
import com.example.payment.dto.PaymentResponse;
import com.example.payment.repository.PaymentRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

@Service
public class PaymentService {

    // Issue: Hardcoded live production secret key
    private String stripeSecretKey = ""; // Read from env

    // Issue: Field injection instead of constructor injection
    @Autowired
    private PaymentRepository paymentRepository;

    // Issue: State-mutating business logic missing @Transactional annotation
    public PaymentResponse executePayment(PaymentRequest request) {
        try {
            // Issue: Potential SQL Injection via string concatenation
            String query = "SELECT * FROM payments WHERE customer_id = '" + request.getCustomerId() + "'";
            paymentRepository.executeRawQuery(query);

            PaymentResponse response = new PaymentResponse();
            response.setStatus("SUCCESS");
            response.setAmount(request.getAmount());

            // Save to repository
            paymentRepository.save(response);
            return response;
        } catch (Exception e) {
            // Issue: Swallowing exception without logging or rethrowing
        }
        return null;
    }

    public PaymentResponse getPaymentById(String id) {
        return paymentRepository.findById(id).orElse(null);
    }
}
