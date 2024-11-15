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
from cl.runtime.primitive.float_util import FloatUtil
from cl.runtime.records.dataclasses_extensions import missing
from cl.convince.llms.gpt.gpt_llm import GptLlm
from cl.convince.prompts.formatted_prompt import FormattedPrompt
from cl.convince.retrievers.annotating_retriever import AnnotatingRetriever
from cl.convince.retrievers.retrieval import Retrieval
from cl.tradeentry.entries.amount_entry import AmountEntry
from cl.tradeentry.entries.currency_entry import CurrencyEntry
from cl.tradeentry.entries.date_entry import DateEntry
from cl.tradeentry.entries.date_or_tenor_entry import DateOrTenorEntry
from cl.tradeentry.entries.day_count_basis_entry import DayCountBasisEntry
from cl.tradeentry.entries.number_entry import NumberEntry
from cl.tradeentry.entries.pay_freq_months_entry import PayFreqMonthsEntry
from cl.tradeentry.entries.pay_receive_entry import PayReceiveEntry
from cl.tradeentry.entries.rates.rates_index_entry import RatesIndexEntry
from cl.tradeentry.entries.rates.swaps.rates_swap_entry import RatesSwapEntry
from cl.tradeentry.trades.currency_key import CurrencyKey
from cl.hackathon.hackathon_input import HackathonInput
from cl.hackathon.hackathon_output import HackathonOutput
from cl.hackathon.hackathon_solution import HackathonSolution


@dataclass(slots=True, kw_only=True)
class AnnotationSolution(HackathonSolution):
    """Solution based on brace annotation of the input."""

    legs_annotation_prompt: str = missing()
    """Prompt to surround information about each leg in curly braces."""

    leg_type_prompt: str = missing()
    """Prompt to determine the leg type."""

    parameter_annotation_prompt: str = missing()
    """Prompt to surround the specified parameter in curly braces."""

    pay_rec_description: str = "The words Buy or Sell, or the words Pay or Receive"
    """Description of the trade side parameter to use with parameter annotation prompt."""

    maturity_description: str = "Either maturity date as a date, or tenor (length) as the number of years and/or months"
    """Description of the maturity tenor or date to use with the parameter annotation prompt."""

    effective_date_description: str = "Effective date as date"
    """Description of the effective date to use with the parameter annotation prompt."""

    freq_months_description: str = "Payment frequency"
    """Description of the payment frequency to use with the parameter annotation prompt."""

    float_index_description: str = "Name of the floating interest rate index"
    """Description of the floating interest rate index to use with the parameter annotation prompt."""

    float_spread_description: str = "Spread over the interest rate index"
    """Description of the floating interest rate spread to use with the parameter annotation prompt."""

    fixed_rate_description: str = "Fixed rate value"
    """Description of the fixed rate value to use with the parameter annotation prompt."""

    notional_description: str = "Trade notional"
    """Description of the trade notional to use with the parameter annotation prompt."""

    basis_description: str = "Day-count basis"
    """Description of the day-count basis to use with the parameter annotation prompt."""

    currency_description: str = "Currency"
    """Description of the currency to use with the parameter annotation prompt."""

    def _extract_notional(self, retriever: AnnotatingRetriever, input_description: str) -> (float, str):
        notional_amount = None
        notional_currency = None

        context = Context.current()
        if extracted_notional := retriever.retrieve(
                input_text=input_description, param_description=self.notional_description, is_required=False
        ):
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

    def _leg_entry_to_dict(self, leg_description: str) -> Dict:
        error_message_prefix = ("Error trying to extract the field from the leg description\n"
                                f"Leg description: {leg_description}\n")

        entry_dict = {}

        retriever = AnnotatingRetriever(
            retriever_id="parameter_annotating_retriever",
            llm=GptLlm(llm_id="gpt-4o"),
            prompt=FormattedPrompt(
                prompt_id="AnnotatingRetriever",
                params_type=Retrieval.__name__,
                template=self.parameter_annotation_prompt,
            ),
        )
        retriever.init_all()

        # Pay or receive flag
        try:
            if extracted_pay_receive := retriever.retrieve(
                    input_text=leg_description, param_description=self.pay_rec_description, is_required=False
            ):
                pay_receive = PayReceiveEntry(text=extracted_pay_receive)
                pay_receive.run_generate()
                if pay_rec_key := pay_receive.pay_receive:
                    entry_dict["pay_receive"] = pay_rec_key.pay_receive_id
        except Exception as e:
            entry_dict["pay_receive"] = error_message_prefix + str(e)

        # Payment Frequency
        try:
            if extracted_freq_months := retriever.retrieve(
                    input_text=leg_description, param_description=self.freq_months_description, is_required=False
            ):
                freq_months = PayFreqMonthsEntry(text=extracted_freq_months)
                freq_months.run_generate()
                entry_dict["freq_months"] = str(FloatUtil.to_int_or_float(v)) if (
                    v := freq_months.pay_freq_months) else None
        except Exception as e:
            entry_dict["freq_months"] = error_message_prefix + str(e)

        # Floating rate index
        try:
            if extracted_float_index := retriever.retrieve(
                input_text=leg_description, param_description=self.float_index_description, is_required=False
            ):
                float_index = RatesIndexEntry(text=extracted_float_index)
                float_index.run_generate()
                if rates_index_key := float_index.rates_index:
                    entry_dict["float_index"] = rates_index_key.rates_index_id
        except Exception as e:
            entry_dict["float_index"] = error_message_prefix + str(e)

        # Floating rate spread
        try:
            if extracted_float_spread := retriever.retrieve(
                input_text=leg_description, param_description=self.float_spread_description, is_required=False
            ):
                float_spread = NumberEntry(text=extracted_float_spread)
                float_spread.run_generate()
                entry_dict["float_spread"] = str(FloatUtil.to_int_or_float(v)) if (v := float_spread.value) else None
        except Exception as e:
            entry_dict["float_spread"] = error_message_prefix + str(e)

        # Day-count Basis
        try:
            if extracted_basis := retriever.retrieve(
                input_text=leg_description, param_description=self.basis_description, is_required=False
            ):
                basis = DayCountBasisEntry(text=extracted_basis)
                basis.run_generate()
                entry_dict["basis"] = basis.basis
        except Exception as e:
            entry_dict["basis"] = error_message_prefix + str(e)

        # Notional
        try:
            notional_amount, notional_currency = self._extract_notional(retriever, leg_description)
            entry_dict["notional_amount"] = notional_amount
            entry_dict["notional_currency"] = notional_currency
        except Exception as e:
            entry_dict["notional_amount"] = error_message_prefix + str(e)
            entry_dict["notional_currency"] = error_message_prefix + str(e)

        # Currency
        try:
            if extracted_currency := retriever.retrieve(
                input_text=leg_description, param_description=self.currency_description, is_required=False
            ):
                currency = CurrencyEntry(text=extracted_currency)
                currency.run_generate()
                if notional_currency_entry_currency_key := currency.currency:
                    notional_currency_entry_currency = Context.current().load_one(
                        CurrencyKey, notional_currency_entry_currency_key
                    )
                    entry_dict["currency"] = notional_currency_entry_currency.iso_code
        except Exception as e:
            entry_dict["currency"] = error_message_prefix + str(e)

        # Fixed Rate
        try:
            if extracted_fixed_rate := retriever.retrieve(
                input_text=leg_description, param_description=self.fixed_rate_description, is_required=False
            ):
                fixed_rate = NumberEntry(text=extracted_fixed_rate)
                fixed_rate.run_generate()
                entry_dict["fixed_rate"] = str(FloatUtil.to_int_or_float(v)) if (v := fixed_rate.value) else None
        except Exception as e:
            entry_dict["fixed_rate"] = error_message_prefix + str(e)

        return entry_dict

    def _retrieve_trade_parameters(self, input_description: str) -> Dict:

        error_message_prefix = ("Error trying to extract the field from the general trade information\n"
                                f"General trade information: {input_description}\n")

        trade_parameters = {}

        retriever = AnnotatingRetriever(
            retriever_id="parameter_annotating_retriever",
            llm=GptLlm(llm_id="gpt-4o"),
            prompt=FormattedPrompt(
                prompt_id="AnnotatingRetriever",
                params_type=Retrieval.__name__,
                template=self.parameter_annotation_prompt,
            ),
        )
        retriever.init_all()

        # Maturity
        try:
            if extracted_maturity := retriever.retrieve(
                input_text=input_description, param_description=self.maturity_description, is_required=False
            ):
                maturity = DateOrTenorEntry(text=extracted_maturity)
                maturity.run_generate()
                if date := maturity.date:
                    trade_parameters["maturity_date"] = date
                else:
                    trade_parameters["tenor_years"] = str(FloatUtil.to_int_or_float(v)) if (
                        v := maturity.years) else None
        except Exception as e:
            trade_parameters["maturity_date"] = error_message_prefix + str(e)
            trade_parameters["tenor_years"] = error_message_prefix + str(e)

        # Effective date
        try:
            if extracted_effective_date := retriever.retrieve(
                    input_text=input_description, param_description=self.effective_date_description, is_required=False
            ):
                effective_date = DateEntry(text=extracted_effective_date)
                effective_date.run_generate()
                if date := effective_date.date:
                    trade_parameters["effective_date"] = date
        except Exception as e:
            trade_parameters["effective_date"] = error_message_prefix + str(e)

        # Notional
        try:
            notional_amount, notional_currency = self._extract_notional(retriever, input_description)
            trade_parameters["notional_amount"] = str(FloatUtil.to_int_or_float(v)) if (v := notional_amount) else None
            trade_parameters["notional_currency"] = notional_currency
        except Exception as e:
            trade_parameters["notional_amount"] = error_message_prefix + str(e)
            trade_parameters["notional_currency"] = error_message_prefix + str(e)

        return trade_parameters

    def _process_input(self, input_: HackathonInput, trial_id: int) -> HackathonOutput:

        output_ = HackathonOutput(
            solution=self.get_key(),
            trade_group=self.trade_group,
            trade_id=input_.trade_id,
            entry_text=input_.entry_text,
        )

        # Extract leg descriptions
        leg_descriptions = RatesSwapEntry(text=input_.entry_text).extract_legs(self.legs_annotation_prompt)

        # Remove each leg description from entry_text in order to get a description of only the general parameters
        general_trade_information = input_.entry_text
        for leg_description in leg_descriptions:
            general_trade_information = general_trade_information.replace(leg_description, "")
        general_trade_information = general_trade_information.strip()

        trade_parameters = self._retrieve_trade_parameters(general_trade_information)

        output_.maturity_date = trade_parameters.get("maturity_date")
        output_.tenor_years = trade_parameters.get("tenor_years")
        output_.effective_date = trade_parameters.get("effective_date")

        notional_amount_str = trade_parameters.get("notional_amount")
        output_.pay_leg_notional = notional_amount_str
        output_.rec_leg_notional = notional_amount_str

        notional_currency = trade_parameters.get("notional_currency")
        output_.pay_leg_ccy = notional_currency
        output_.rec_leg_ccy = notional_currency

        for leg_description in leg_descriptions:
            self._populate_leg(output_, leg_description)

        return output_

    def _populate_leg(self, trade: HackathonOutput, description: str):

        leg_entry_dict = self._leg_entry_to_dict(description)
        pay_receive = leg_entry_dict.get("pay_receive")

        if pay_receive == "Pay":
            trade.pay_leg_notional = leg_entry_dict.get("notional_amount")
            trade.pay_leg_ccy = leg_entry_dict.get("notional_currency")
            trade.pay_leg_basis = leg_entry_dict.get("basis")
            trade.pay_leg_freq_months = leg_entry_dict.get("freq_months")
            trade.pay_leg_float_index = leg_entry_dict.get("float_index")
            trade.pay_leg_float_spread_bp = leg_entry_dict.get("float_spread")
            trade.pay_leg_fixed_rate_pct = leg_entry_dict.get("fixed_rate")
            trade.pay_leg_ccy = leg_entry_dict.get("currency")
        elif pay_receive == "Receive":
            trade.rec_leg_notional = leg_entry_dict.get("notional_amount")
            trade.rec_leg_ccy = leg_entry_dict.get("notional_currency")
            trade.rec_leg_basis = leg_entry_dict.get("basis")
            trade.rec_leg_freq_months = leg_entry_dict.get("freq_months")
            trade.rec_leg_float_index = leg_entry_dict.get("float_index")
            trade.rec_leg_float_spread_bp = leg_entry_dict.get("float_spread")
            trade.rec_leg_fixed_rate_pct = leg_entry_dict.get("fixed_rate")
            trade.rec_leg_ccy = leg_entry_dict.get("currency")
        else:
            # TODO (Kate): Message for the case when pay_receive is None.

            trade.pay_leg_notional = pay_receive
            trade.pay_leg_ccy = pay_receive
            trade.pay_leg_basis = pay_receive
            trade.pay_leg_freq_months = pay_receive
            trade.pay_leg_float_index = pay_receive
            trade.pay_leg_float_spread_bp = pay_receive
            trade.pay_leg_fixed_rate_pct = pay_receive
            trade.rec_leg_notional = pay_receive
            trade.rec_leg_ccy = pay_receive
            trade.rec_leg_basis = pay_receive
            trade.rec_leg_freq_months = pay_receive
            trade.rec_leg_float_index = pay_receive
            trade.rec_leg_float_spread_bp = pay_receive
            trade.rec_leg_fixed_rate_pct = pay_receive
