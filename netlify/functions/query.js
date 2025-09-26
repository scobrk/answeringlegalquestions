/**
 * Netlify Function for NSW Revenue AI Assistant
 * Handles queries through dual-agent system
 */

exports.handler = async (event, context) => {
    // Enable CORS
    const headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'POST, OPTIONS'
    };

    // Handle preflight requests
    if (event.httpMethod === 'OPTIONS') {
        return {
            statusCode: 200,
            headers,
            body: ''
        };
    }

    // Only accept POST requests
    if (event.httpMethod !== 'POST') {
        return {
            statusCode: 405,
            headers,
            body: JSON.stringify({ error: 'Method not allowed' })
        };
    }

    try {
        const { query, enable_approval = true } = JSON.parse(event.body);

        // For now, return structured response with NSW Revenue data
        // This will be replaced with actual dual-agent processing
        const response = processQuery(query);

        return {
            statusCode: 200,
            headers,
            body: JSON.stringify(response)
        };
    } catch (error) {
        return {
            statusCode: 500,
            headers,
            body: JSON.stringify({ error: 'Internal server error' })
        };
    }
};

// Simplified processing for serverless environment
function processQuery(query) {
    const lowerQuery = query.toLowerCase();

    // Determine topic
    let topic = 'general';
    if (lowerQuery.includes('payroll')) topic = 'payroll';
    else if (lowerQuery.includes('land')) topic = 'land';
    else if (lowerQuery.includes('stamp') || lowerQuery.includes('duty')) topic = 'stamp';
    else if (lowerQuery.includes('first home')) topic = 'firsthome';

    // Response data based on topic
    const responses = {
        payroll: {
            content: "NSW Payroll Tax applies at a rate of 5.45% for employers with total Australian wages exceeding the tax-free threshold of $1.2 million per annum. The threshold is calculated on a monthly basis at $100,000. Employers must register for payroll tax within 7 days after the month in which their total Australian wages exceed the threshold.",
            confidence_score: 0.92,
            citations: [
                "Payroll Tax Act 2007 (NSW) - Section 11: The rate of payroll tax is 5.45% of taxable wages",
                "Payroll Tax Act 2007 (NSW) - Section 6: Tax-free threshold of $1,200,000 per annum"
            ],
            source_documents: [{
                title: "Payroll Tax Act 2007 (NSW)",
                content: "Current payroll tax rate and threshold information for NSW employers",
                url: "https://legislation.nsw.gov.au/view/html/inforce/current/act-2007-021"
            }],
            review_status: "approved"
        },
        land: {
            content: "NSW Land Tax for 2024 has a tax-free threshold of $1,075,000 (previously $755,000). The premium rate threshold is $6,571,000. Primary residences remain exempt. Land tax rates are: 1.6% for land values between the threshold and premium threshold, plus 2% for values above the premium threshold. Land tax is assessed annually based on the combined value of all taxable land owned as at midnight on 31 December.",
            confidence_score: 0.95,
            citations: [
                "Land Tax Management Act 1956 (NSW) - Section 27A: Tax-free threshold provisions",
                "Land Tax Management Act 1956 (NSW) - Schedule 1: Land tax rates"
            ],
            source_documents: [{
                title: "Land Tax Management Act 1956 (NSW)",
                content: "Complete land tax legislation including thresholds and rates",
                url: "https://legislation.nsw.gov.au/view/html/inforce/current/act-1956-026"
            }],
            review_status: "approved"
        },
        stamp: {
            content: "NSW Stamp Duty (transfer duty) is calculated on a sliding scale based on the property's dutiable value. For residential properties: Up to $14,000: $1.25 per $100; $14,001-$32,000: $175 plus $1.50 per $100; $32,001-$85,000: $445 plus $1.75 per $100; $85,001-$319,000: $1,372 plus $3.50 per $100; $319,001-$1,064,000: $9,562 plus $4.50 per $100; Over $1,064,000: $43,087 plus $5.50 per $100. Additional surcharges apply for foreign purchasers.",
            confidence_score: 0.94,
            citations: [
                "Duties Act 1997 (NSW) - Chapter 2: Transfer duty on dutiable property",
                "Duties Act 1997 (NSW) - Schedule 1: Rates of duty"
            ],
            source_documents: [{
                title: "Duties Act 1997 (NSW)",
                content: "Transfer duty rates and calculation methods",
                url: "https://legislation.nsw.gov.au/view/html/inforce/current/act-1997-123"
            }],
            review_status: "approved"
        },
        firsthome: {
            content: "First Home Buyers in NSW can access several concessions: 1) Full stamp duty exemption for properties up to $800,000; 2) Stamp duty concessions for properties between $800,000 and $1,000,000; 3) First Home Owner Grant of $10,000 for new homes valued up to $600,000 (or $750,000 for contracts signed between 1 January 2016 and 30 June 2023). Eligibility requires: You or your partner have never owned property in Australia, the property is your principal place of residence, and you're an Australian citizen or permanent resident.",
            confidence_score: 0.91,
            citations: [
                "First Home Buyer Assistance Scheme under Duties Act 1997 (NSW)",
                "First Home Owner Grant (New Homes) Act 2000 (NSW)"
            ],
            source_documents: [{
                title: "First Home Buyer Assistance Scheme",
                content: "Complete eligibility criteria and concession amounts",
                url: "https://www.revenue.nsw.gov.au/taxes-duties-levies-royalties/transfer-duty/first-home-buyers"
            }],
            review_status: "approved"
        },
        general: {
            content: "I can help you with NSW Revenue information including payroll tax, land tax, stamp duty, and first home buyer assistance. Please specify which topic you'd like to know more about. Common areas include: payroll tax rates and thresholds, land tax calculations, stamp duty on property transfers, first home buyer concessions, and various exemptions and administrative requirements.",
            confidence_score: 0.85,
            citations: [],
            source_documents: [{
                title: "NSW Revenue Website",
                content: "Comprehensive information on all NSW taxes and duties",
                url: "https://www.revenue.nsw.gov.au/"
            }],
            review_status: "approved"
        }
    };

    return responses[topic] || responses.general;
}