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
from typing import Dict, List

from cl.hackathon.hackathon_input import HackathonInput
from cl.runtime import Context
from cl.runtime.log.exceptions.user_error import UserError
from cl.runtime.records.dataclasses_extensions import missing
from cl.convince.llms.gpt.gpt_llm import GptLlm
from cl.convince.prompts.formatted_prompt import FormattedPrompt
from cl.convince.retrievers.annotating_retriever import AnnotatingRetriever
from cl.convince.retrievers.retrieval import Retrieval
from cl.tradeentry.entries.amount_entry import AmountEntry
from cl.tradeentry.entries.currency_entry import CurrencyEntry
from cl.tradeentry.entries.date_entry import DateEntry
from cl.tradeentry.entries.date_or_tenor_entry import DateOrTenorEntry
from cl.tradeentry.entries.number_entry import NumberEntry
from cl.tradeentry.entries.pay_freq_entry import PayFreqEntry
from cl.tradeentry.entries.pay_receive_entry import PayReceiveEntry
from cl.tradeentry.entries.rates.rates_index_entry import RatesIndexEntry
from cl.tradeentry.entries.rates.swaps.any_leg_entry import AnyLegEntry
from cl.tradeentry.entries.rates.swaps.rates_swap_entry import RatesSwapEntry
from cl.tradeentry.trades.currency_key import CurrencyKey
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

    pay_freq_description: str = "Payment frequency"
    """Description of the payment frequency to use with the parameter annotation prompt."""

    float_freq_description: str = "Frequency at which floating interest accrues"
    """Description of the floating frequency to use with the parameter annotation prompt."""

    float_index_description: str = "Name of the floating interest rate index"
    """Description of the floating interest rate index to use with the parameter annotation prompt."""

    float_spread_description: str = "Spread over the interest rate index"
    """Description of the floating interest rate spread to use with the parameter annotation prompt."""

    fixed_rate_description: str = "Fixed rate value"
    """Description of the fixed rate value to use with the parameter annotation prompt."""

    notional_description: str = "Trade notional"
    """Description of the trade notional to use with the parameter annotation prompt."""

    def _float_leg_entry_to_dict(self, leg_description) -> Dict:

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
        if extracted_pay_receive := retriever.retrieve(
            input_text=leg_description, param_description=self.pay_rec_description, is_required=False
        ):
            pay_receive = PayReceiveEntry(description=extracted_pay_receive)
            pay_receive.run_generate()
            if pay_rec_key := pay_receive.pay_receive:
                entry_dict["pay_receive"] = pay_rec_key.pay_receive_id

        # Payment Frequency
        if extracted_pay_freq := retriever.retrieve(
            input_text=leg_description, param_description=self.pay_freq_description, is_required=False
        ):
            # TODO: Reformat description
            entry_dict["pay_freq"] = extracted_pay_freq

        # Floating Frequency
        if extracted_float_freq := retriever.retrieve(
            input_text=leg_description, param_description=self.float_freq_description, is_required=False
        ):
            # TODO: Reformat description
            entry_dict["float_freq"] = extracted_float_freq

        # Floating rate index
        if extracted_float_index := retriever.retrieve(
            input_text=leg_description, param_description=self.float_index_description, is_required=False
        ):
            float_index = RatesIndexEntry(description=extracted_float_index)
            float_index.run_generate()
            if rates_index_key := float_index.rates_index:
                entry_dict["float_index"] = rates_index_key.rates_index_id

        # Floating rate spread
        if extracted_float_spread := retriever.retrieve(
            input_text=leg_description, param_description=self.float_spread_description, is_required=False
        ):
            float_spread = NumberEntry(description=extracted_float_spread)
            float_spread.run_generate()
            entry_dict["float_spread"] = float_spread.value

        return entry_dict

    def _fixed_leg_entry_to_dict(self, leg_description) -> Dict:

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
        if extracted_pay_receive := retriever.retrieve(
            input_text=leg_description, param_description=self.pay_rec_description, is_required=False
        ):
            pay_receive = PayReceiveEntry(description=extracted_pay_receive)
            pay_receive.run_generate()
            if pay_rec_key := pay_receive.pay_receive:
                entry_dict["pay_receive"] = pay_rec_key.pay_receive_id

        # Payment Frequency
        if extracted_pay_freq := retriever.retrieve(
            input_text=leg_description, param_description=self.pay_freq_description, is_required=False
        ):
            pay_freq = PayFreqEntry(description=extracted_pay_freq)
            # TODO: Reformat description
            entry_dict["pay_freq"] = extracted_pay_freq

        # Fixed Rate
        if extracted_fixed_rate := retriever.retrieve(
            input_text=leg_description, param_description=self.fixed_rate_description, is_required=False
        ):
            fixed_rate = NumberEntry(description=extracted_fixed_rate)
            fixed_rate.run_generate()
            entry_dict["fixed_rate"] = fixed_rate.value

        return entry_dict

    def _retrieve_trade_parameters(self, input_: HackathonInput) -> Dict:

        trade_parameters = {}

        context = Context.current()
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
        if extracted_maturity := retriever.retrieve(
            input_text=input_.entry_text, param_description=self.maturity_description, is_required=False
        ):
            maturity = DateOrTenorEntry(description=extracted_maturity)
            maturity.run_generate()
            if date := maturity.date:
                trade_parameters["maturity_date"] = date
            else:
                tenor_parts = []

                if maturity.years is not None:
                    tenor_parts.append(f"{maturity.years}y")
                if maturity.months is not None:
                    tenor_parts.append(f"{maturity.months}m")
                if maturity.weeks is not None:
                    tenor_parts.append(f"{maturity.weeks}w")
                if maturity.days is not None:
                    tenor_parts.append(f"{maturity.days}d")
                if maturity.business_days is not None:
                    tenor_parts.append(f"{maturity.business_days}b")

                # TODO: Convert to date
                if tenor_parts:
                    trade_parameters["maturity_date"] = "".join(tenor_parts)

        # Effective date
        if extracted_effective_date := retriever.retrieve(
            input_text=input_.entry_text, param_description=self.effective_date_description, is_required=False
        ):
            effective_date = DateEntry(description=extracted_effective_date)
            effective_date.run_generate()
            if date := effective_date.date:
                trade_parameters["effective_date"] = date

        # Notional
        if extracted_notional := retriever.retrieve(
            input_text=input_.entry_text, param_description=self.notional_description, is_required=False
        ):
            notional = AmountEntry(description=extracted_notional)
            notional.run_generate()

            if notional_amount_entry_key := notional.amount:
                notional_amount_entry = context.load_one(NumberEntry, notional_amount_entry_key)
                notional_amount_entry.run_generate()
                trade_parameters["notional_amount"] = notional_amount_entry.value

            if notional_currency_entry_key := notional.currency:
                notional_currency_entry = context.load_one(CurrencyEntry, notional_currency_entry_key)

                if notional_currency_entry_currency_key := notional_currency_entry.currency:
                    notional_currency_entry_currency = context.load_one(
                        CurrencyKey, notional_currency_entry_currency_key
                    )
                    trade_parameters["notional_currency"] = notional_currency_entry_currency.iso_code

        return trade_parameters

    def _process_input(self, input_: HackathonInput) -> HackathonOutput:

        # TODO (Roman): Do we need a trade group as part of the HackathonOutputKey if it is already in the solution?
        output_ = HackathonOutput(
            solution=self.get_key(),
            trade_group=self.trade_group,
            trade_id=input_.trade_id,
            entry_text=input_.entry_text,
        )

        trade_parameters = self._retrieve_trade_parameters(input_)

        output_.maturity_date = trade_parameters.get("maturity_date")
        output_.effective_date = trade_parameters.get("effective_date")

        # TODO (Roman): 'HackathonOutput' class has no attributes 'notional_amount' and 'notional_currency' or similar.
        # output_.notional_amount = trade_parameters.get("notional_amount")
        # output_.notional_currency = trade_parameters.get("notional_currency")

        leg_descriptions = RatesSwapEntry(description=input_.entry_text).extract_legs(self.legs_annotation_prompt)

        # TODO (Roman): Check if it is critical to have exactly 2 legs in leg_descriptions list.
        # if len(leg_descriptions) != 2:
        #     raise UserError(
        #         f"Incorrect number of legs. Should be 2.\n" f"Leg descriptions:\n" f"{' '.join(leg_descriptions)}"
        #     )

        for leg_description in leg_descriptions:
            self._populate_leg(output_, leg_description)

        return output_

    def _get_ids_list(self) -> List[int] | None:
        # TODO (Roman): Extract list from self.trade_ids attribute.
        return None

    def run_generate(self) -> None:

        # Load all inputs
        inputs = Context.current().load_all(HackathonInput)

        # Filter inputs by trade_group and trade_ids
        inputs = [
            x for x in inputs
            if x.trade_group == self.trade_group and
            ((ids_list := self._get_ids_list()) is None or x.trade_id in ids_list)
        ]

        # Process inputs
        for input_ in inputs:
            output_ = self._process_input(input_)
            Context.current().save_one(output_)

        Context.current().save_one(self)

    def _populate_leg(self, trade: HackathonOutput, description: str):
        leg_type = AnyLegEntry(description=description).determine_leg_type(self.leg_type_prompt)
        if leg_type == "Floating":
            leg_entry_dict = self._float_leg_entry_to_dict(description)
            pay_receive = leg_entry_dict.get("pay_receive")

            # TODO (Roman): Review pay_freq. It's a string in dict (e.g. "semi-annual"), but int in class declaration.
            try:
                pay_freq = int(leg_entry_dict.get("pay_freq"))
            except Exception:
                pay_freq = None

            if pay_receive == "Pay":
                trade.pay_leg_freq_months = pay_freq
                # TODO (Roman): 'HackathonOutput' class has no attribute 'pay_leg_float_freq' or similar.
                # trade.pay_leg_float_freq = leg_entry_dict.get("float_freq")
                trade.pay_leg_float_index = leg_entry_dict.get("float_index")
                trade.pay_leg_float_spread_bp = leg_entry_dict.get("float_spread")
            elif pay_receive == "Receive":
                trade.rec_leg_freq_months = pay_freq
                # TODO (Roman): 'HackathonOutput' class has no attribute 'rec_leg_float_freq' or similar.
                # trade.rec_leg_float_freq = leg_entry_dict.get("float_freq")
                trade.rec_leg_float_index = leg_entry_dict.get("float_index")
                trade.rec_leg_float_spread_bp = leg_entry_dict.get("float_spread")
            else:
                raise UserError(f"Unknown value of pay_receive parameter: {pay_receive}")
        elif leg_type == "Fixed":
            leg_entry_dict = self._fixed_leg_entry_to_dict(description)
            pay_receive = leg_entry_dict.get("pay_receive")

            # TODO (Roman): Review pay_freq. It's a string in dict (e.g. "semi-annual"), but int in class declaration.
            try:
                pay_freq = int(leg_entry_dict.get("pay_freq"))
            except Exception:
                pay_freq = None

            if pay_receive == "Pay":
                trade.pay_leg_freq_months = pay_freq
                trade.pay_leg_fixed_rate_pct = leg_entry_dict.get("fixed_rate")
            elif pay_receive == "Receive":
                trade.rec_leg_freq_months = pay_freq
                trade.rec_leg_fixed_rate_pct = leg_entry_dict.get("fixed_rate")
            else:
                # TODO (Roman): Check whether to raise an error if pay_receive is None or something else
                # raise UserError(f"Unknown value of pay_receive parameter: {pay_receive}")
                pass
        else:
            raise UserError(f"Undefined leg type: {leg_type}")
