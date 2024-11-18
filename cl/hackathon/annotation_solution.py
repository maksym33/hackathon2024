# Copyright (C) 2023-present The Project Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from dataclasses import dataclass
from typing import Dict
from cl.runtime import Context
from cl.runtime.experiments.trial_key import TrialKey
from cl.runtime.log.exceptions.user_error import UserError
from cl.runtime.primitive.float_util import FloatUtil
from cl.runtime.records.dataclasses_extensions import missing
from cl.convince.prompts.formatted_prompt import FormattedPrompt
from cl.convince.retrievers.annotating_retriever import AnnotatingRetriever
from cl.convince.retrievers.retrieval import Retrieval
from cl.tradeentry.entries.amount_entry import AmountEntry
from cl.tradeentry.entries.currency_entry import CurrencyEntry
from cl.tradeentry.entries.date_entry import DateEntry
from cl.tradeentry.entries.date_or_tenor_entry import DateOrTenorEntry
from cl.tradeentry.entries.number_entry import NumberEntry
from cl.tradeentry.entries.pay_freq_months_entry import PayFreqMonthsEntry
from cl.tradeentry.trades.currency_key import CurrencyKey
from cl.hackathon.hackathon_input import HackathonInput
from cl.hackathon.hackathon_output import HackathonOutput
from cl.hackathon.hackathon_solution import HackathonSolution
from cl.hackathon.our_gpt_client import GPTClient


BUDGET = 0


FEATURES ={
    'params':
    [
        "maturity_date",
        "tenor_years",
        "effective_date",
        ],
    'leg': # extracted twice for pay and receive leg
        [
        "notional_amount",
        "notional_currency",
        "basis",
        "freq_months",
        "float_index",
        "float_spread",
        "fixed_rate",
        "currency"
    ]
}

@dataclass(slots=True, kw_only=True)
class AnnotationSolution(HackathonSolution):
    """Solution based on brace annotation of the input."""

    parameter_annotation_prompt: str = missing()
    """Prompt to surround the specified parameter in curly braces."""

    maturity_description: str = "Either maturity date as a date, or tenor (length) as the number of years and/or months. Do not include the word 'tenor' in the solution."
    """Description of the maturity tenor or date."""

    effective_date_description: str = (
        "The effective date is the start date of the swap agreement, marking the beginning of the contract's "
        "terms and the first date from which interest payments will accrue. It is the date when the swap becomes "
        "active, and the two parties officially start exchanging cash flows according to the agreed terms." +\
        "Wrap only the date in, for example in YY/MM/DD format. If not possible/applicable, leave text as is."
    )
    """Description of the effective date."""

    freq_months_description: str = (
        "Payment frequency defines how often the interest payments are exchanged between the parties involved in "
        "the swap. This frequency is commonly expressed in intervals such as monthly, quarterly, semi-annually, or annually. "
        "The frequency determines the regularity of cash flows and is a key parameter in structuring the swap." + \
        "Wrap your chosen answer as if an integer, without any suffixes or prefixes. If not possible/applicable, leave it empty."

    )
    """Description of the payment frequency."""

    float_index_description: str = (
        "The floating interest rate index is a reference benchmark rate used to determine the floating leg of the swap. "
        "Common indices include LIBOR (London Interbank Offered Rate), SOFR (Secured Overnight Financing Rate), and EURIBOR "
        "(Euro Interbank Offered Rate). This index serves as the foundation for calculating the variable payments in the swap." + \
        "Wrap your answer like 'SOFR', 'EURIBOR' or even '6M Term SOFR' if possible. If not possible/applicable, leave it empty."

    )
    """Description of the floating interest rate index."""

    float_spread_description: str = (
        "The floating rate spread is an additional margin or percentage added to the floating interest rate index "
        "to calculate the total floating rate payment. It is often agreed upon at the inception of the contract and reflects "
        "factors such as credit risk or market conditions. The spread adjusts the base index rate to account for these variables." + \
        "Wrap your answer as just a float/int, like 35.0 or 4, without the 'bs' suffix. If not possible/applicable, leave it empty."

    )
    """Description of the floating interest rate spread."""

    fixed_rate_description: str = (
        "The fixed rate is the predetermined and agreed-upon interest rate that applies to the fixed leg of the swap. "
        "This rate remains constant throughout the duration of the swap and is used to calculate fixed interest payments. "
        "It is typically based on prevailing market conditions at the time the swap is executed." + \
        "Wrap your answer as just a float. If not possible/applicable, leave it empty."
    )
    """Description of the fixed rate value."""

    notional_description: str = "Trade notional"
    """Description of the trade notional."""

    basis_description: str = (
        "The day-count basis is the convention used to calculate accrued interest in the swap. Common conventions "
        "include '30/360', which assumes 30 days in each month and 360 days in a year, 'Actual/360', which uses the actual "
        "number of days in a month and divides by 360, and 'Actual/365', which accounts for the actual days in a year. "
        "The day-count basis is critical for accurately determining the amount of interest owed during each payment period." + \
        "Wrap your answer as a string. If not possible/applicable, leave it empty."
    )
    """Description of the day-count basis."""

    currency_description: str = (
        "The currency refers to the denomination in which the notional amount and interest payments are expressed. "
        "Major currencies commonly used in swaps include the US Dollar (USD), Euro (EUR), and British Pound (GBP). "
        "The choice of currency often depends on the parties' financial needs and market conditions." + \
        "Wrap your answer as a string, like 'GBP', 'EUR' or 'USD'. If not possible/applicable, leave it empty."
    )
    """Description of the currency."""

    def _extract_notional(self, retriever: AnnotatingRetriever, input_description: str, leg_type: str) -> (float, str):
        notional_amount = None
        notional_currency = None
        context = Context.current()

        param_description = self.notional_description + f" for the {leg_type}"
        if extracted_notional := retriever.retrieve(input_text=input_description, param_description=param_description):
            notional = AmountEntry(text=extracted_notional)
            notional.run_generate()

            if notional_amount_entry_key := notional.amount:
                notional_amount_entry = context.load_one(NumberEntry, notional_amount_entry_key)
                notional_amount_entry.run_generate()
                notional_amount = notional_amount_entry.value

            if notional_currency_entry_key := notional.currency:
                notional_currency_entry = context.load_one(CurrencyEntry, notional_currency_entry_key)

                if notional_currency_entry_currency_key := notional_currency_entry.currency:
                    notional_currency_entry_currency = context.load_one(
                        CurrencyKey, notional_currency_entry_currency_key
                    )
                    notional_currency = notional_currency_entry_currency.iso_code

        return notional_amount, notional_currency

    def _leg_entry_to_dict(self, retriever: AnnotatingRetriever, trade_description: str, leg_type: str, required_fields=None) -> Dict:
        retriever_error_message_prefix = (
            f"Error trying to extract the field from the trade description\nTrade description: {trade_description}\n"
        )

        entry_error_message_template = (
            "Error trying to process an extracted field from the trade description\n"
            "Extracted field: {extracted_field}\n"
            f"Trade description: {trade_description}\n"
            "{exception_message}"
        )

        param_description_suffix = f" for the {leg_type}"

        entry_dict = {}

        def extract_freq_months():
            # Payment Frequency
            extracted_freq_months = None
            try:
                extracted_freq_months = retriever.retrieve(
                    input_text=trade_description, param_description=self.freq_months_description + param_description_suffix
                )
            except Exception as e:
                entry_dict["freq_months"] = retriever_error_message_prefix + str(e)

            if extracted_freq_months is not None:
                try:
                    freq_months = PayFreqMonthsEntry(text=extracted_freq_months)
                    freq_months.run_generate()
                    entry_dict["freq_months"] = (
                        str(FloatUtil.to_int_or_float(v)) if (v := freq_months.pay_freq_months) else None
                    )
                except Exception as e:
                    entry_dict["freq_months"] = entry_error_message_template.format(
                        extracted_field=extracted_freq_months, exception_message=str(e)
                    )
        def extract_floating_rate():
            # Floating rate index
            try:
                extracted_float_index = retriever.retrieve(
                    input_text=trade_description, param_description=self.float_index_description + param_description_suffix
                )
                entry_dict["float_index"] = extracted_float_index
            except Exception as e:
                entry_dict["float_index"] = retriever_error_message_prefix + str(e)

        def extract_float_spread():
            # Floating rate spread
            extracted_float_spread = None
            try:
                extracted_float_spread = retriever.retrieve(
                    input_text=trade_description, param_description=self.float_spread_description + param_description_suffix
                )
            except Exception as e:
                entry_dict["float_spread"] = retriever_error_message_prefix + str(e)

            if extracted_float_spread is not None:
                try:
                    float_spread = NumberEntry(text=extracted_float_spread)
                    float_spread.run_generate()
                    entry_dict["float_spread"] = str(FloatUtil.to_int_or_float(v)) if (v := float_spread.value) else None
                except Exception as e:
                    entry_dict["float_spread"] = entry_error_message_template.format(
                        extracted_field=extracted_float_spread, exception_message=str(e)
                    )

        def extract_basis():
            # Day-count Basis
            try:
                extracted_basis = retriever.retrieve(
                    input_text=trade_description, param_description=self.basis_description + param_description_suffix
                )
                entry_dict["basis"] = extracted_basis
            except Exception as e:
                entry_dict["basis"] = retriever_error_message_prefix + str(e)

        def extract_notional():
            # Notional
            try:
                notional_amount, notional_currency = self._extract_notional(retriever, trade_description, leg_type)
                entry_dict["notional_amount"] = str(FloatUtil.to_int_or_float(v)) if (v := notional_amount) else None
                entry_dict["notional_currency"] = notional_currency
            except Exception as e:
                entry_dict["notional_amount"] = retriever_error_message_prefix + str(e)
                entry_dict["notional_currency"] = retriever_error_message_prefix + str(e)

        def extract_ccy():
            # Currency
            extracted_currency = None
            try:
                extracted_currency = retriever.retrieve(
                    input_text=trade_description, param_description=self.currency_description + param_description_suffix
                )
            except Exception as e:
                entry_dict["currency"] = retriever_error_message_prefix + str(e)

            if extracted_currency is not None:
                try:
                    currency = CurrencyEntry(text=extracted_currency)
                    currency.run_generate()
                    if notional_currency_entry_currency_key := currency.currency:
                        notional_currency_entry_currency = Context.current().load_one(
                            CurrencyKey, notional_currency_entry_currency_key
                        )
                        entry_dict["currency"] = notional_currency_entry_currency.iso_code
                except Exception as e:
                    entry_dict["currency"] = entry_error_message_template.format(
                        extracted_field=extracted_currency, exception_message=str(e)
                    )

        def extract_fixed_rate():
            # Fixed Rate
            extracted_fixed_rate = None
            try:
                extracted_fixed_rate = retriever.retrieve(
                    input_text=trade_description, param_description=self.fixed_rate_description + param_description_suffix
                )
            except Exception as e:
                entry_dict["fixed_rate"] = retriever_error_message_prefix + str(e)

            if extracted_fixed_rate is not None:
                try:
                    fixed_rate = NumberEntry(text=extracted_fixed_rate)
                    fixed_rate.run_generate()
                    entry_dict["fixed_rate"] = str(FloatUtil.to_int_or_float(v)) if (v := fixed_rate.value) else None
                except Exception as e:
                    entry_dict["fixed_rate"] = entry_error_message_template.format(
                        extracted_field=extracted_fixed_rate, exception_message=str(e)
                    )

        if required_fields is None:
            extract_freq_months()
            extract_floating_rate()
            extract_float_spread()
            extract_basis()
            extract_notional()
            extract_ccy()
            extract_fixed_rate()
            return entry_dict

        if "notional_amount" in required_fields or "notional_currency" in required_fields:
            extract_notional()

        if "basis" in required_fields:
            extract_basis()

        if "freq_months" in required_fields:
            extract_freq_months()

        if "float_index" in required_fields:
            extract_floating_rate()

        if "float_spread" in required_fields:
            extract_float_spread()

        if "fixed_rate" in required_fields:
            extract_fixed_rate()

        if "currency" in required_fields:
            extract_ccy()

        return entry_dict

    def _retrieve_trade_parameters(self, retriever: AnnotatingRetriever, input_description: str, required_fields=None) -> Dict:

        error_message_prefix = (
            "Error trying to extract the field from the trade description\n" f"Trade description: {input_description}\n"
        )

        entry_error_message_template = (
            "Error trying to process an extracted field from the trade description\n"
            "Extracted field: {extracted_field}\n"
            f"Trade description: {input_description}\n"
            "{exception_message}"
        )

        trade_parameters = {}


        def extract_maturity_or_tenor():
            # Maturity
            extracted_maturity = None
            try:
                extracted_maturity = retriever.retrieve(
                    input_text=input_description, param_description=self.maturity_description
                )
            except Exception as e:
                trade_parameters["maturity_date"] = error_message_prefix + str(e)
                trade_parameters["tenor_years"] = error_message_prefix + str(e)

            if extracted_maturity is not None:
                try:
                    maturity = DateOrTenorEntry(text=extracted_maturity)
                    maturity.run_generate()
                    if date := maturity.date:
                        trade_parameters["maturity_date"] = date
                    else:
                        trade_parameters["tenor_years"] = (
                            str(FloatUtil.to_int_or_float(v)) if (v := maturity.years) else None
                        )
                except Exception as e:
                    formatted_error_message = entry_error_message_template.format(
                        extracted_field=extracted_maturity, exception_message=str(e)
                    )

                    trade_parameters["maturity_date"] = formatted_error_message
                    trade_parameters["tenor_years"] = formatted_error_message

        def extract_effective_date():
            # Effective date
            extracted_effective_date = None
            try:
                extracted_effective_date = retriever.retrieve(
                    input_text=input_description, param_description=self.effective_date_description
                )
            except Exception as e:
                trade_parameters["effective_date"] = error_message_prefix + str(e)

            if extracted_effective_date is not None:
                try:
                    effective_date = DateEntry(text=extracted_effective_date)
                    effective_date.run_generate()
                    if date := effective_date.date:
                        trade_parameters["effective_date"] = date
                except Exception as e:
                    trade_parameters["effective_date"] = entry_error_message_template.format(
                        extracted_field=extracted_effective_date, exception_message=str(e)
                    )

        if required_fields is None:
            extract_maturity_or_tenor()
            extract_effective_date()
            return trade_parameters

        if "maturity_date" in required_fields or "tenor_years" in required_fields:
            extract_maturity_or_tenor()
        if "effective_date" in required_fields:
            extract_effective_date()

        return trade_parameters

    def score_output(self, output_: HackathonOutput) -> None:

        if Context.current().trial is not None:
            raise UserError("Cannot override TrialId that is already set, exiting.")  # TODO: Append?

        with Context(full_llm=self.llm, trial=TrialKey(trial_id=str(output_.trial_id))) as context:

            retriever = AnnotatingRetriever(
                retriever_id=f"{self.solution_id}::{self.trade_group}::{output_.trade_id}::{output_.trial_id}",
                prompt=FormattedPrompt(
                    prompt_id="AnnotatingRetriever",
                    params_type=Retrieval.__name__,
                    template=self.parameter_annotation_prompt,
                ),
            )
            retriever.init_all()
            Context.current().save_one(retriever)

            params_trials = []
            pay_leg_trials = []
            receive_leg_trials = []

            trade_parameters = self._retrieve_trade_parameters(retriever, output_.entry_text)
            pay_leg_parameters = self._leg_entry_to_dict(retriever, output_.entry_text, "Pay leg")
            rec_leg_parameters = self._leg_entry_to_dict(retriever, output_.entry_text, "Receive leg")

            params_trials.append(trade_parameters)
            pay_leg_trials.append(pay_leg_parameters)
            receive_leg_trials.append(rec_leg_parameters)

            while BUDGET > 0:

                n_params, params_to_rerun = get_params_to_rerun()
                n_pays, pay_params_to_rerun = get_params_to_rerun()
                n_recs, rec_params_to_rerun = get_params_to_rerun()

                if (n_params or 3) + (n_pays or 8) + (n_recs or 8) < BUDGET:
                    break

                trade_parameters = self._retrieve_trade_parameters(retriever, output_.entry_text, params_to_rerun)
                pay_leg_parameters = self._leg_entry_to_dict(retriever, output_.entry_text, "Pay leg", pay_params_to_rerun)
                receive_leg_trials = self._leg_entry_to_dict(retriever, output_.entry_text, "Receive leg", rec_params_to_rerun)

                params_trials.append(trade_parameters)
                pay_leg_trials.append(pay_leg_parameters)
                receive_leg_trials.append(receive_leg_trials)

            trade_parameters = manage_conflicts(params_trials)
            pay_leg_parameters = manage_conflicts(pay_leg_trials)
            rec_leg_parameters = manage_conflicts(receive_leg_trials)

            output_ = _update_output_object(output_, trade_parameters, pay_leg_parameters, rec_leg_parameters)


def get_params_to_rerun(*args):
    return None, None


def manage_conflicts(output_list):
    return output_list[0]


def _update_output_object(output_, trade_parameters, pay_leg_parameters, rec_leg_parameters):
        output_.maturity_date = trade_parameters.get("maturity_date")
        output_.tenor_years = trade_parameters.get("tenor_years")
        output_.effective_date = trade_parameters.get("effective_date")

        # Populate pay leg
        output_.pay_leg_notional = pay_leg_parameters.get("notional_amount")
        output_.pay_leg_ccy = pay_leg_parameters.get("notional_currency")
        output_.pay_leg_basis = pay_leg_parameters.get("basis")
        output_.pay_leg_freq_months = pay_leg_parameters.get("freq_months")
        output_.pay_leg_float_index = pay_leg_parameters.get("float_index")
        output_.pay_leg_float_spread_bp = pay_leg_parameters.get("float_spread")
        output_.pay_leg_fixed_rate_pct = pay_leg_parameters.get("fixed_rate")
        output_.pay_leg_ccy = pay_leg_parameters.get("currency")

        # Populate receive leg
        output_.rec_leg_notional = rec_leg_parameters.get("notional_amount")
        output_.rec_leg_ccy = rec_leg_parameters.get("notional_currency")
        output_.rec_leg_basis = rec_leg_parameters.get("basis")
        output_.rec_leg_freq_months = rec_leg_parameters.get("freq_months")
        output_.rec_leg_float_index = rec_leg_parameters.get("float_index")
        output_.rec_leg_float_spread_bp = rec_leg_parameters.get("float_spread")
        output_.rec_leg_fixed_rate_pct = rec_leg_parameters.get("fixed_rate")
        output_.rec_leg_ccy = rec_leg_parameters.get("currency")

        return output_

