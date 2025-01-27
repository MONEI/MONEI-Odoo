CANCEL_PAYMENT_MUTATION = """
mutation CancelPayment($input: CancelPaymentInput!) {
  cancelPayment(input: $input) {
    id
    status
    statusCode
    statusMessage
    cancellationReason
    updatedAt
  }
}
"""

REFUND_PAYMENT_MUTATION = """
mutation RefundPayment($input: RefundPaymentInput!) {
    refundPayment(input: $input) {
        id
        status
        statusCode
        statusMessage
        refundedAmount
        lastRefundAmount
        lastRefundReason
        updatedAt
    }
}
"""

CAPTURE_PAYMENT_MUTATION = """
mutation CapturePayment($input: CapturePaymentInput!) {
    capturePayment(input: $input) {
        id
        status
        statusCode
        statusMessage
        amount
        updatedAt
    }
}
"""

CREATE_PAYMENT_MUTATION = """
mutation CreatePayment($input: CreatePaymentInput!) {
    createPayment(input: $input) {
        id
        status
        statusCode
        statusMessage
        amount
        currency
        orderId
        description
        customer {
            name
            email
            phone
        }
        updatedAt
    }
}
"""

SEND_PAYMENT_LINK_MUTATION = """
mutation SendPaymentLink($input: SendPaymentMessageInput!) {
    sendPaymentLink(input: $input) {
        id
    }
}
"""