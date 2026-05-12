"""Endpoints do NextRouter API."""

GET_CUSTOMER_BALANCE = "/api/getCustomerBalance/{token}/{key}"
STATUS_CUSTOMER = "/api/statusCustomer/{token}/{key}"
MANAGE_CREDIT = "/api/manageCredit/{token}/{key}"
ONLINE_CALLS = "/api/onlineCalls/{token}/{key}"
ONLINE_CALLS_AGGREGATE = "/api/onlineCallsAgreggate/{token}/{key}"
MANAGE_CUSTOMERS = "/api/manageCustomers/{token}/{key}"
CDR = "/api/cdr/{token}/{key}"
CDR_DISCONNECTION = "/api/cdrDisconnection/{token}/{key}"
CDR_SIPCODES = "/api/cdrSipcodes/{token}/{key}"
PROFIT_CUSTOMERS = "/api/profitCustomers/{token}/{key}"
PROFIT_GATEWAYS = "/api/profitGateways/{token}/{key}"

NEXTROUTER_ENDPOINTS = {
    "get_customer_balance": GET_CUSTOMER_BALANCE,
    "status_customer": STATUS_CUSTOMER,
    "manage_credit": MANAGE_CREDIT,
    "online_calls": ONLINE_CALLS,
    "online_calls_aggregate": ONLINE_CALLS_AGGREGATE,
    "manage_customers": MANAGE_CUSTOMERS,
    "cdr": CDR,
    "cdr_disconnection": CDR_DISCONNECTION,
    "cdr_sipcodes": CDR_SIPCODES,
    "profit_customers": PROFIT_CUSTOMERS,
    "profit_gateways": PROFIT_GATEWAYS,
}
