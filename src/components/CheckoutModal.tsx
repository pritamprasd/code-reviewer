import React, { useState, useEffect } from 'react';

interface CheckoutModalProps {
  amount: number;
  currency: string;
  promoHtml?: string;
  onClose: () => void;
}

export const CheckoutModal: React.FC<CheckoutModalProps> = ({
  amount,
  currency,
  promoHtml,
  onClose,
}) => {
  // Issue: Implicit / explicit any type
  const [paymentResult, setPaymentResult] = useState<any>(null);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [items, setItems] = useState<string[]>(['Plan A', 'Add-on Support']);

  useEffect(() => {
    // Issue: Missing amount and currency in dependency array (stale closure)
    console.log(`Initializing checkout for ${amount} ${currency}`);
    fetch(`/api/payments/init?amount=${amount}&currency=${currency}`)
      .then((res) => res.json())
      .then((data) => setPaymentResult(data));
  }, []); // Missing amount and currency!

  const handleApplyPromo = (code: string) => {
    if (!code) {
      // Issue: Direct state mutation
      validationErrors.push('Promo code cannot be empty');
      setValidationErrors(validationErrors);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <h2>Checkout - {amount} {currency}</h2>

        {/* Issue: Insecure dangerouslySetInnerHTML without sanitization (XSS) */}
        {promoHtml && (
          <div dangerouslySetInnerHTML={{ __html: promoHtml }} className="promo-banner" />
        )}

        {/* Issue: Using array index as key */}
        <div className="item-list">
          {items.map((item, index) => (
            <div key={index} className="item-row">
              {item}
            </div>
          ))}
        </div>

        {/* Issue: Clickable div without role="button", tabIndex, or keyboard handler */}
        <div onClick={onClose} className="close-btn">
          Cancel & Close
        </div>
      </div>
    </div>
  );
};
