CHARGES_QUERY = """
query {
    charges%s {
        items {
            id
            accountId
            providerId
            checkoutId
            providerInternalId
            providerReferenceId
            createdAt
            updatedAt
            amount
            authorizationCode
            billingDetails {
                email
                name
                company
                phone
                address {
                    city
                    country
                    line1
                    line2
                    zip
                    state
                }
                taxId
            }
            billingPlan
            currency
            customer {
                email
                name
                phone
            }
            description
            descriptor
            livemode
            orderId
            storeId
            pointOfSaleId
            terminalId
            sequenceId
            subscriptionId
            paymentMethod {
                method
                card {
                    brand
                    country
                    type
                    threeDSecure
                    threeDSecureVersion
                    threeDSecureFlow
                    last4
                    cardholderName
                    cardholderEmail
                    expiration
                    bank
                    tokenizationMethod
                }
                cardPresent {
                    brand
                    country
                    type
                    bin
                    last4
                    cardholderName
                    cardholderEmail
                    expiration
                }
                bizum {
                    phoneNumber
                    integrationType
                }
                paypal {
                    orderId
                    payerId
                    email
                    name
                }
                cofidis {
                    orderId
                }
                cofidisLoan {
                    orderId
                }
                trustly {
                    customerId
                }
                sepa {
                    accountholderAddress {
                        city
                        country
                        line1
                        line2
                        zip
                        state
                    }
                    accountholderEmail
                    accountholderName
                    countryCode
                    bankAddress
                    bankCode
                    bankName
                    bic
                    last4
                }
                klarna {
                    billingCategory
                    authPaymentMethod
                }
                mbway {
                    phoneNumber
                }
            }
            cancellationReason
            lastRefundAmount
            lastRefundReason
            refundedAmount
            shippingDetails {
                email
                name
                company
                phone
                address {
                    city
                    country
                    line1
                    line2
                    zip
                    state
                }
                taxId
            }
            shop {
                name
                country
            }
            status
            statusCode
            statusMessage
            sessionDetails {
                ip
                userAgent
                countryCode
                lang
                deviceType
                deviceModel
                browser
                browserVersion
                browserAccept
                browserColorDepth
                browserScreenHeight
                browserScreenWidth
                browserTimezoneOffset
                os
                osVersion
                source
                sourceVersion
            }
            traceDetails {
                ip
                userAgent
                countryCode
                lang
                deviceType
                deviceModel
                browser
                browserVersion
                browserAccept
                os
                osVersion
                source
                sourceVersion
                userId
                userEmail
                userName
            }
            pageOpenedAt
            metadata {
                key
                value
            }
        }
        total
    }
}
"""

ACCOUNT_QUERY = """
query Account{
    account {
        apiKey
    }
}
""" 

STORES_QUERY = """
query Stores{
    stores {
        items {
            id
            name
        }
    }
}
"""

PAYMENT_METHODS_QUERY = """
query AvailablePaymentMethods {
    availablePaymentMethods {
        paymentMethod
        configured
        enabled
    }
}
"""

CHARGE_QUERY = """
query Charge($id: ID!) {
    charge(id: $id) {
        id
        accountId
        providerId
        checkoutId
        providerInternalId
        providerReferenceId
        createdAt
        updatedAt
        amount
        authorizationCode
        billingDetails {
            email
            name
            company
            phone
            address {
                city
                country
                line1
                line2
                zip
                state
            }
            taxId
        }
        billingPlan
        currency
        customer {
            email
            name
            phone
        }
        description
        descriptor
        livemode
        orderId
        storeId
        pointOfSaleId
        terminalId
        sequenceId
        subscriptionId
        paymentMethod {
            method
            card {
                brand
                country
                type
                threeDSecure
                threeDSecureVersion
                threeDSecureFlow
                last4
                cardholderName
                cardholderEmail
                expiration
                bank
                tokenizationMethod
            }
            cardPresent {
                brand
                country
                type
                bin
                last4
                cardholderName
                cardholderEmail
                expiration
            }
            bizum {
                phoneNumber
                integrationType
            }
            paypal {
                orderId
                payerId
                email
                name
            }
            cofidis {
                orderId
            }
            cofidisLoan {
                orderId
            }
            trustly {
                customerId
            }
            sepa {
                accountholderAddress {
                    city
                    country
                    line1
                    line2
                    zip
                    state
                }
                accountholderEmail
                accountholderName
                countryCode
                bankAddress
                bankCode
                bankName
                bic
                last4
            }
            klarna {
                billingCategory
                authPaymentMethod
            }
            mbway {
                phoneNumber
            }
        }
        cancellationReason
        lastRefundAmount
        lastRefundReason
        refundedAmount
        shippingDetails {
            email
            name
            company
            phone
            address {
                city
                country
                line1
                line2
                zip
                state
            }
            taxId
        }
        shop {
            name
            country
        }
        status
        statusCode
        statusMessage
        sessionDetails {
            ip
            userAgent
            countryCode
            lang
            deviceType
            deviceModel
            browser
            browserVersion
            browserAccept
            browserColorDepth
            browserScreenHeight
            browserScreenWidth
            browserTimezoneOffset
            os
            osVersion
            source
            sourceVersion
        }
        traceDetails {
            ip
            userAgent
            countryCode
            lang
            deviceType
            deviceModel
            browser
            browserVersion
            browserAccept
            os
            osVersion
            source
            sourceVersion
            userId
            userEmail
            userName
        }
        pageOpenedAt
        metadata {
            key
            value
        }
    }
}
"""