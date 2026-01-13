from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
import math

app = FastAPI(title="Financial Calculators API")

@app.get("/")
def root():
    return {"status": "ok"}
# ---------------- SIP ----------------

class SIPInput(BaseModel):
    monthly_sip: float
    years: int
    annual_return: float

def sip_calculator(monthly_sip, years, annual_return):
    monthly_r = (1 + annual_return / 100) ** (1 / 12) - 1
    months = years * 12

    corpus = 0
    total_invested = monthly_sip * months

    for _ in range(months):
        corpus = (corpus + monthly_sip) * (1 + monthly_r)

    return {
        "maturity_value": round(corpus, 0),
        "total_invested": round(total_invested, 0),
        "wealth_gained": round(corpus - total_invested, 0),
        "multiple": round(corpus / total_invested, 2)
    }

@app.post("/sip")
def sip_api(data: SIPInput):
    return sip_calculator(
        data.monthly_sip,
        data.years,
        data.annual_return
    )
# ---------------- SIP STEP-UP ----------------

class SIPStepUpInput(BaseModel):
    monthly_sip: float
    years: int
    annual_return: float
    annual_step_up: float

def sip_step_up_calculator(monthly_sip, years, annual_return, annual_step_up):
    monthly_r = (1 + annual_return / 100) ** (1 / 12) - 1
    total_months = years * 12

    corpus = 0
    total_invested = 0
    current_sip = monthly_sip

    for month in range(1, total_months + 1):
        if month > 1 and (month - 1) % 12 == 0:
            current_sip *= (1 + annual_step_up / 100)

        corpus = (corpus + current_sip) * (1 + monthly_r)
        total_invested += current_sip

    return {
        "maturity_value": round(corpus, 0),
        "total_invested": round(total_invested, 0),
        "wealth_gained": round(corpus - total_invested, 0),
        "multiple": round(corpus / total_invested, 2)
    }

@app.post("/sip-step-up")
def sip_step_up_api(data: SIPStepUpInput):
    return sip_step_up_calculator(
        data.monthly_sip,
        data.years,
        data.annual_return,
        data.annual_step_up
    )
# ---------------- EMI ----------------

class EMIInput(BaseModel):
    loan_amount: float
    tenure_years: int
    annual_interest_rate: float

def emi_calculator(loan_amount, tenure_years, annual_interest_rate):
    r = annual_interest_rate / 100 / 12
    n = tenure_years * 12

    if r == 0:
        emi = loan_amount / n
    else:
        emi = loan_amount * r * ((1 + r) ** n) / ((1 + r) ** n - 1)

    total_payment = emi * n
    total_interest = total_payment - loan_amount

    return {
        "emi": round(emi, 0),
        "total_payment": round(total_payment, 0),
        "total_interest": round(total_interest, 0)
    }

@app.post("/emi")
def emi_api(data: EMIInput):
    return emi_calculator(
        data.loan_amount,
        data.tenure_years,
        data.annual_interest_rate
    )
# ---------------- SIP TENURE ----------------

class SIPTenureInput(BaseModel):
    target_amount: float
    monthly_sip: float
    annual_return: float

def sip_tenure_calculator(target_amount, monthly_sip, annual_return):
    monthly_r = (1 + annual_return / 100) ** (1 / 12) - 1

    corpus = 0
    months = 0
    total_invested = 0

    # Safety cap: 60 years
    max_months = 60 * 12

    while corpus < target_amount and months < max_months:
        corpus = (corpus + monthly_sip) * (1 + monthly_r)
        total_invested += monthly_sip
        months += 1

    years_required = math.ceil(months / 12)

    return {
        "years_required": years_required,
        "total_months": months,
        "total_invested": round(total_invested, 0),
        "final_corpus": round(corpus, 0)
    }

@app.post("/sip-tenure")
def sip_tenure_api(data: SIPTenureInput):
    return sip_tenure_calculator(
        data.target_amount,
        data.monthly_sip,
        data.annual_return
    )
# ---------------- LUMPSUM ----------------

class LumpsumInput(BaseModel):
    amount: float
    years: int
    annual_return: float
    inflation: Optional[float] = None

def lumpsum_calculator(amount, years, annual_return, inflation=None):
    # Monthly compounding for consistency
    monthly_r = (1 + annual_return / 100) ** (1 / 12) - 1
    months = years * 12

    future_value = amount * ((1 + monthly_r) ** months)

    result = {
        "future_value": round(future_value, 0)
    }

    # Inflation-adjusted value (real value)
    if inflation is not None:
        monthly_i = (1 + inflation / 100) ** (1 / 12) - 1
        real_value = future_value / ((1 + monthly_i) ** months)
        result["inflation_adjusted_value"] = round(real_value, 0)

    return result

@app.post("/lumpsum")
def lumpsum_api(data: LumpsumInput):
    return lumpsum_calculator(
        data.amount,
        data.years,
        data.annual_return,
        data.inflation
    )
# ---------------- EDUCATION GOAL ----------------

class EducationInput(BaseModel):
    child_age: int
    college_age: int
    education_duration_years: int
    annual_cost_today: float
    existing_corpus: float
    investment_return: float
    education_inflation: float


def education_calculator(
    child_age,
    college_age,
    education_duration_years,
    annual_cost_today,
    existing_corpus,
    investment_return,
    education_inflation
):
    # Years until college starts
    years_to_college = college_age - child_age

    # Step 1: Inflate annual cost till college
    inflated_annual_cost = annual_cost_today * (
        (1 + education_inflation / 100) ** years_to_college
    )

    # Step 2: Inflate cost during education years
    total_required = 0
    for year in range(education_duration_years):
        total_required += inflated_annual_cost * (
            (1 + education_inflation / 100) ** year
        )

    # Step 3: Grow existing corpus till college (annual compounding)
    existing_corpus_future = existing_corpus * (
        (1 + investment_return / 100) ** years_to_college
    )

    # Step 4: Gap to be funded
    gap = max(0, total_required - existing_corpus_future)

    # Step 5: Lump sum required today
    lump_sum_today = gap / (
        (1 + investment_return / 100) ** years_to_college
    ) if gap > 0 else 0

    # Step 6: Monthly SIP required (annuity due)
    monthly_r = investment_return / 100 / 12
    months = years_to_college * 12

    sip_factor = ((1 + monthly_r) ** months - 1) / monthly_r
    sip_factor_due = sip_factor * (1 + monthly_r)

    monthly_sip = gap / sip_factor_due if gap > 0 else 0

    return {
        "goal_at_college": {
            "total_required": round(total_required, 0)
        },
        "existing_corpus": {
            "today": existing_corpus,
            "value_at_college": round(existing_corpus_future, 0)
        },
        "investment_required": {
            "lump_sum_today": round(lump_sum_today, 0),
            "monthly_sip": round(monthly_sip, 0)
        }
    }


@app.post("/education-goal")
def education_api(data: EducationInput):
    return education_calculator(
        data.child_age,
        data.college_age,
        data.education_duration_years,
        data.annual_cost_today,
        data.existing_corpus,
        data.investment_return,
        data.education_inflation
    )
# ---------------- RETIREMENT GOAL ----------------

class RetirementInput(BaseModel):
    current_age: int
    retirement_age: int
    life_expectancy: int
    current_monthly_expense: float
    inflation_rate: float
    current_monthly_saving: float
    existing_corpus: float
    pre_retirement_return: float
    post_retirement_return: float


def retirement_calculator(
    current_age,
    retirement_age,
    life_expectancy,
    current_monthly_expense,
    inflation_rate,
    current_monthly_saving,
    existing_corpus,
    pre_retirement_return,
    post_retirement_return
):
    years_to_retirement = retirement_age - current_age
    retirement_years = life_expectancy - retirement_age

    # Step 1: Monthly expense at retirement
    monthly_expense_at_retirement = current_monthly_expense * (
        (1 + inflation_rate / 100) ** years_to_retirement
    )
    annual_expense_at_retirement = monthly_expense_at_retirement * 12

    # Step 2: Corpus required at retirement (real return)
    real_return = ((1 + post_retirement_return / 100) /
                   (1 + inflation_rate / 100)) - 1

    corpus_required = annual_expense_at_retirement * (
        (1 - (1 + real_return) ** (-retirement_years)) / real_return
    )

    # Step 3: Future value of existing corpus
    fv_existing = existing_corpus * (
        (1 + pre_retirement_return / 100) ** years_to_retirement
    )

    # Step 4: Future value of current SIP (annuity due)
    monthly_r = pre_retirement_return / 100 / 12
    months = years_to_retirement * 12

    sip_fv = current_monthly_saving * (
        ((1 + monthly_r) ** months - 1) / monthly_r
    ) * (1 + monthly_r)

    total_available = fv_existing + sip_fv

    # Step 5: Shortfall
    shortfall = max(0, corpus_required - total_available)

    # Step 6: Required SIP and Lumpsum
    sip_required = shortfall / (
        ((1 + monthly_r) ** months - 1) / monthly_r * (1 + monthly_r)
    ) if shortfall > 0 else 0

    lump_sum_required = shortfall / (
        (1 + pre_retirement_return / 100) ** years_to_retirement
    ) if shortfall > 0 else 0

    return {
        "monthly_expense_at_retirement": round(monthly_expense_at_retirement, 0),
        "corpus_required": round(corpus_required, 0),
        "total_available": round(total_available, 0),
        "shortfall": round(shortfall, 0),
        "investment_required": {
            "sip": round(sip_required, 0),
            "lumpsum": round(lump_sum_required, 0)
        }
    }


@app.post("/retirement-goal")
def retirement_api(data: RetirementInput):
    return retirement_calculator(
        data.current_age,
        data.retirement_age,
        data.life_expectancy,
        data.current_monthly_expense,
        data.inflation_rate,
        data.current_monthly_saving,
        data.existing_corpus,
        data.pre_retirement_return,
        data.post_retirement_return
    )
# ---------------- MARRIAGE GOAL ----------------

class MarriageInput(BaseModel):
    current_age: int
    marriage_age: int
    marriage_cost_today: float
    existing_corpus: float
    investment_return: float
    cost_inflation: float


def marriage_calculator(
    current_age,
    marriage_age,
    marriage_cost_today,
    existing_corpus,
    investment_return,
    cost_inflation
):
    years_to_goal = marriage_age - current_age

    # Inflate marriage cost till goal year
    inflated_cost = marriage_cost_today * (
        (1 + cost_inflation / 100) ** years_to_goal
    )

    # Grow existing corpus
    existing_corpus_future = existing_corpus * (
        (1 + investment_return / 100) ** years_to_goal
    )

    gap = max(0, inflated_cost - existing_corpus_future)

    # Lump sum required today
    lump_sum_today = gap / (
        (1 + investment_return / 100) ** years_to_goal
    ) if gap > 0 else 0

    # Monthly SIP required (annuity due)
    monthly_r = investment_return / 100 / 12
    months = years_to_goal * 12

    sip_factor = ((1 + monthly_r) ** months - 1) / monthly_r
    sip_factor_due = sip_factor * (1 + monthly_r)

    monthly_sip = gap / sip_factor_due if gap > 0 else 0

    return {
        "goal_amount": round(inflated_cost, 0),
        "existing_corpus": {
            "today": existing_corpus,
            "value_at_goal": round(existing_corpus_future, 0)
        },
        "investment_required": {
            "lump_sum_today": round(lump_sum_today, 0),
            "monthly_sip": round(monthly_sip, 0)
        }
    }


@app.post("/marriage-goal")
def marriage_api(data: MarriageInput):
    return marriage_calculator(
        data.current_age,
        data.marriage_age,
        data.marriage_cost_today,
        data.existing_corpus,
        data.investment_return,
        data.cost_inflation
    )
# ---------------- COST OF DELAY SIP ----------------

class CostOfDelayInput(BaseModel):
    monthly_sip: float
    years: int
    annual_return: float
    delay_months: int


def sip_future_value(monthly_sip, months, annual_return):
    monthly_r = (1 + annual_return / 100) ** (1 / 12) - 1
    corpus = 0

    for _ in range(months):
        corpus = (corpus + monthly_sip) * (1 + monthly_r)

    return corpus


def cost_of_delay_calculator(
    monthly_sip,
    years,
    annual_return,
    delay_months
):
    total_months = years * 12

    # Start now
    fv_start_now = sip_future_value(
        monthly_sip,
        total_months,
        annual_return
    )

    # Start late
    fv_start_late = sip_future_value(
        monthly_sip,
        total_months - delay_months,
        annual_return
    )

    total_invested_now = monthly_sip * total_months
    total_invested_late = monthly_sip * (total_months - delay_months)

    return {
        "start_now": {
            "maturity_value": round(fv_start_now, 0),
            "amount_invested": round(total_invested_now, 0),
            "wealth_gained": round(fv_start_now - total_invested_now, 0)
        },
        "start_late": {
            "delay_months": delay_months,
            "maturity_value": round(fv_start_late, 0),
            "amount_invested": round(total_invested_late, 0),
            "wealth_gained": round(fv_start_late - total_invested_late, 0)
        },
        "cost_of_delay": round(fv_start_now - fv_start_late, 0)
    }


@app.post("/cost-of-delay-sip")
def cost_of_delay_api(data: CostOfDelayInput):
    return cost_of_delay_calculator(
        data.monthly_sip,
        data.years,
        data.annual_return,
        data.delay_months
    )