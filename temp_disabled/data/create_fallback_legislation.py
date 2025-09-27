"""
Create fallback NSW Revenue legislation content
Generates structured content for local vector search
"""

import os
import json
from pathlib import Path
import time

def create_nsw_revenue_legislation():
    """Create structured NSW Revenue legislation content"""

    # Create data directory
    data_dir = Path("./data/legislation")
    data_dir.mkdir(parents=True, exist_ok=True)

    # NSW Revenue Acts content
    legislation_content = {
        "duties_act_1997": """
Duties Act 1997 (NSW)

PART 2 - CONVEYANCE DUTY

Section 31 - Rate of conveyance duty
The rate of conveyance duty on a conveyance of dutiable property (other than a conveyance to which section 32 applies) is:
(a) for consideration not exceeding $14,000—$1.25 for each $100, or part of $100, of the consideration
(b) for consideration exceeding $14,000 but not exceeding $32,000—$175 plus $1.50 for each $100, or part of $100, of the consideration in excess of $14,000
(c) for consideration exceeding $32,000 but not exceeding $83,000—$270 plus $1.75 for each $100, or part of $100, of the consideration in excess of $32,000
(d) for consideration exceeding $83,000 but not exceeding $319,000—$1,162.50 plus $3.50 for each $100, or part of $100, of the consideration in excess of $83,000
(e) for consideration exceeding $319,000 but not exceeding $1,059,000—$9,422.50 plus $4.50 for each $100, or part of $100, of the consideration in excess of $319,000
(f) for consideration exceeding $1,059,000—$42,722.50 plus $5.50 for each $100, or part of $100, of the consideration in excess of $1,059,000

Section 54 - Concessional duty for first home buyers
A conveyance of a home to a first home buyer is exempt from duty if the consideration for the conveyance does not exceed $650,000.
If the consideration exceeds $650,000 but does not exceed $800,000, the duty payable is reduced by the amount calculated using the formula: $25,000 − ($25,000 × ((consideration − $650,000) ÷ $150,000))

Section 163 - What is dutiable property
Dutiable property means:
(a) land in New South Wales, or
(b) goods in New South Wales, or
(c) a chose in action that relates to property referred to in paragraph (a) or (b), or
(d) a chose in action that relates to a business carried on wholly or partly in New South Wales

PART 3 - MORTGAGE DUTY

Section 203 - Liability for mortgage duty
Mortgage duty is chargeable on a mortgage of dutiable property.

Section 204 - Rate of mortgage duty
The rate of mortgage duty is $4 for each $1,000, or part of $1,000, of the amount secured.
""",

        "payroll_tax_act_2007": """
Payroll Tax Act 2007 (NSW)

Section 11 - Liability for payroll tax
(1) Payroll tax is imposed on an employer whose taxable wages paid or payable in Australia in a financial year exceed the tax-free threshold.
(2) Payroll tax is imposed on the amount of taxable wages that exceeds the tax-free threshold.

Section 15 - Rate of payroll tax
The rate of payroll tax is 5.45%.

Section 5 - Tax-free threshold
(1) The tax-free threshold for a financial year is $1,200,000.
(2) If an employer is a member of a group, the tax-free threshold is to be apportioned among the members of the group in accordance with an agreement between the members or, if there is no agreement, equally among the members.

Section 6 - Meaning of wages
(1) Wages includes any payment made to or for an employee by way of:
(a) salary, wage, commission, bonus or allowance, or
(b) payment for leave of absence, or
(c) fee, commission, bonus or similar payment under a contract for the performance of work, or
(d) payment to a religious practitioner by a religious institution, or
(e) remuneration of a director of a company.

(2) Wages includes the value of any benefit provided to or for an employee.
(3) Wages includes any amount that is salary or wages for the purposes of the Pay-roll Tax Assessment Act 1941 of the Commonwealth.

Section 7 - Meaning of employer
An employer includes:
(a) any person who pays or is liable to pay wages, and
(b) any person who would be liable to pay wages but for an arrangement to avoid liability for payroll tax.

Section 39 - Monthly returns and payments
(1) An employer who is liable to pay payroll tax must lodge a monthly return.
(2) The return must be lodged by the 7th day of the month following the month to which the return relates.
(3) Payroll tax must be paid when the return is lodged.
""",

        "land_tax_act_1956": """
Land Tax Act 1956 (NSW)

Section 3A - Principal place of residence exemption
(1) Land used and occupied by the owner as the owner's principal place of residence is exempt from land tax.
(2) The exemption under subsection (1) applies to so much of the land as does not exceed 2 hectares in area.
(3) Only one principal place of residence exemption may be claimed by a person in any land tax year.
(4) A person who owns land jointly with another person may claim the principal place of residence exemption if the land is used and occupied by the person as the person's principal place of residence.

Section 9A - Tax-free threshold
The tax-free threshold for land tax is $969,000 for the 2024 land tax year.

Section 27 - Rate of land tax
Land tax is charged on the taxable value of land at the following rates:
(a) For taxable value not exceeding $969,000: nil
(b) For taxable value exceeding $969,000 but not exceeding $4,488,000: 1.6% of the taxable value exceeding $969,000
(c) For taxable value exceeding $4,488,000: $56,304 plus 2.0% of the taxable value exceeding $4,488,000

Section 10CA - Premium property tax
(1) Premium property tax is charged on land if the taxable value of the land exceeds $5,000,000.
(2) The rate of premium property tax is 2% of the taxable value of the land exceeding $5,000,000.

Section 3B - Pensioner exemption
(1) Land used and occupied by a pensioner as the pensioner's principal place of residence is exempt from land tax.
(2) The exemption applies if the pensioner's income does not exceed the prescribed amount.
(3) The exemption applies to so much of the land as does not exceed 2 hectares in area.
""",

        "land_tax_management_act_1956": """
Land Tax Management Act 1956 (NSW)

Section 10 - Principal place of residence exemption
(1) An application for a principal place of residence exemption must be made to the Chief Commissioner.
(2) The application must be in a form approved by the Chief Commissioner.
(3) The Chief Commissioner may require the applicant to provide evidence supporting the application.

Section 27 - Assessment of land tax
(1) The Chief Commissioner must assess the land tax payable for each parcel of land.
(2) The assessment must specify the taxable value of the land and the amount of land tax payable.
(3) The Chief Commissioner must give notice of the assessment to the owner of the land.

Section 51 - Objections against assessments
(1) A person who is dissatisfied with an assessment may object to the assessment.
(2) An objection must be lodged within 60 days after the notice of assessment is given.
(3) An objection must be in writing and must specify the grounds of objection.

Section 65 - Appeals to Land and Environment Court
(1) A person who is dissatisfied with a decision on an objection may appeal to the Land and Environment Court.
(2) An appeal must be commenced within 28 days after notice of the decision is given.

Section 74 - Recovery of land tax
(1) Land tax that is due and payable is a debt due to the Crown.
(2) Land tax may be recovered by action in a court of competent jurisdiction.
(3) If land tax remains unpaid for 12 months after it becomes due and payable, the Chief Commissioner may apply to the Supreme Court for an order for the sale of the land.
""",

        "revenue_administration_act_1996": """
Revenue Administration Act 1996 (NSW)

Section 12 - Functions of Chief Commissioner
The functions of the Chief Commissioner include:
(a) the administration of taxation laws, and
(b) the collection of taxes, and
(c) the investigation of matters relating to taxation laws, and
(d) the provision of advice to the Treasurer on matters relating to taxation laws.

Section 44 - Assessment powers
(1) The Chief Commissioner may make an assessment of the amount of tax payable by a person.
(2) An assessment may be made whether or not a return has been lodged.
(3) The Chief Commissioner may amend an assessment at any time.

Section 87 - Objections
(1) A person who is dissatisfied with an assessment or decision may object to the assessment or decision.
(2) An objection must be lodged within 60 days after notice of the assessment or decision is given.
(3) The Chief Commissioner must consider the objection and either allow it wholly or partly or disallow it.

Section 96 - Appeals
(1) A person who is dissatisfied with a decision on an objection may appeal to the Supreme Court.
(2) An appeal must be commenced within 28 days after notice of the decision is given.

Section 108 - General anti-avoidance provision
(1) This section applies if the Chief Commissioner is satisfied that a person has entered into or carried out a scheme for the purpose of avoiding tax.
(2) The Chief Commissioner may make such adjustments as the Chief Commissioner considers appropriate to counteract any tax advantage obtained or obtainable by the person.

Section 117 - Record keeping requirements
(1) A person who is required to pay tax must keep records that explain all transactions and other acts engaged in by the person that are relevant for taxation purposes.
(2) Records must be kept for at least 5 years after completion of the transactions or acts to which they relate.
""",

        "fines_act_1996": """
Fines Act 1996 (NSW)

Section 16 - Payment of penalty notices
(1) The penalty prescribed by a penalty notice is payable within 28 days after the penalty notice is served.
(2) A penalty notice may specify a lesser period within which the penalty is to be paid.

Section 24 - Election to have penalty notice dealt with by court
(1) A person on whom a penalty notice has been served may elect to have the matter dealt with by a court.
(2) An election must be made within 28 days after the penalty notice is served.
(3) An election must be made by completing and returning the appropriate part of the penalty notice.

Section 35 - Enforcement action
(1) If a penalty prescribed by a penalty notice is not paid within the time specified in the notice, enforcement action may be taken.
(2) Enforcement action includes:
(a) the making of an enforcement order, and
(b) the suspension or cancellation of a licence, and
(c) the seizure and sale of property, and
(d) garnishment of wages or bank accounts.

Section 48 - Enforcement orders
(1) Revenue NSW may make an enforcement order if a fine is not paid when due.
(2) An enforcement order may direct that:
(a) the person's driver licence be suspended, or
(b) the person's vehicle registration be suspended, or
(c) the person be prohibited from applying for or renewing a licence.

Section 65 - Work and development orders
(1) Revenue NSW may make a work and development order in relation to a fine.
(2) A work and development order allows the fine to be satisfied by completing unpaid work, courses, treatment or other activities.
(3) The order must specify the number of hours of unpaid work or other activities to be completed.
""",

        "first_home_owner_grant_2000": """
First Home Owner Grant (New Homes) Act 2000 (NSW)

Section 8 - Eligibility for grant
(1) A natural person is eligible for a first home owner grant if:
(a) the person is a natural person who is an Australian citizen or permanent resident, and
(b) the person is at least 18 years of age, and
(c) the person has not previously received a first home owner grant or similar grant, and
(d) the person has not previously owned residential property in Australia, and
(e) the person enters into a contract to purchase or build a new home, and
(f) the contract price does not exceed $750,000.

Section 9 - Amount of grant
(1) The amount of the first home owner grant is $10,000.
(2) If the home is located in a regional area, an additional grant of $5,000 may be available.

Section 12 - Residence requirement
(1) The applicant must occupy the home as their principal place of residence for a continuous period of at least 6 months.
(2) The 6-month period must commence within 12 months after completion of the home.

Section 15 - Application for grant
(1) An application for a first home owner grant must be made to Revenue NSW.
(2) The application must be in the approved form and must be accompanied by the required documents.
(3) The application must be made within 12 months after completion of the home.

Section 18 - Recovery of grant
(1) Revenue NSW may recover the whole or part of a first home owner grant if:
(a) the grant was paid in error, or
(b) the applicant provided false or misleading information, or
(c) the applicant fails to comply with the residence requirement.

Section 21 - Offences
(1) A person who provides false or misleading information in an application is guilty of an offence.
(2) Maximum penalty: 50 penalty units or imprisonment for 6 months, or both.
"""
    }

    # Save each act to a separate file
    for act_key, content in legislation_content.items():
        file_path = data_dir / f"{act_key}.txt"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content.strip())
        print(f"✅ Created {file_path} ({len(content)} chars)")

    # Save metadata
    metadata = {
        "acts": list(legislation_content.keys()),
        "created_at": time.time(),
        "total_acts": len(legislation_content),
        "description": "NSW Revenue legislation for AI assistant",
        "act_details": {
            "duties_act_1997": {"full_name": "Duties Act 1997 (NSW)", "sections": 6},
            "payroll_tax_act_2007": {"full_name": "Payroll Tax Act 2007 (NSW)", "sections": 5},
            "land_tax_act_1956": {"full_name": "Land Tax Act 1956 (NSW)", "sections": 5},
            "land_tax_management_act_1956": {"full_name": "Land Tax Management Act 1956 (NSW)", "sections": 5},
            "revenue_administration_act_1996": {"full_name": "Revenue Administration Act 1996 (NSW)", "sections": 6},
            "fines_act_1996": {"full_name": "Fines Act 1996 (NSW)", "sections": 5},
            "first_home_owner_grant_2000": {"full_name": "First Home Owner Grant (New Homes) Act 2000 (NSW)", "sections": 5}
        }
    }

    metadata_path = data_dir / "metadata.json"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)

    print(f"✅ Created metadata at {metadata_path}")
    print(f"\n📁 All files saved to: {data_dir}")
    print(f"📊 Total acts: {len(legislation_content)}")

    return legislation_content

if __name__ == "__main__":
    create_nsw_revenue_legislation()