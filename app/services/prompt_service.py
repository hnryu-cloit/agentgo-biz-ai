from app.prompts.templates import ANALYSIS_PROMPTS, OPERATIONS_PROMPTS, STRATEGY_PROMPTS


class PromptService:
    def build_analysis_prompt(self, prompt_type: str, context: str) -> str:
        return ANALYSIS_PROMPTS[prompt_type].format(context=context)

    def build_strategy_prompt(self, prompt_type: str, context: str) -> str:
        return STRATEGY_PROMPTS[prompt_type].format(context=context)

    def build_operations_prompt(self, prompt_type: str, context: str) -> str:
        return OPERATIONS_PROMPTS[prompt_type].format(context=context)

    def render_analysis_summary(self, prompt_type: str, context: str, lead: str) -> str:
        self.build_analysis_prompt(prompt_type, context)
        return lead

    def render_strategy_summary(self, prompt_type: str, context: str, lead: str) -> str:
        self.build_strategy_prompt(prompt_type, context)
        return lead

    def render_operations_summary(self, prompt_type: str, context: str, lead: str) -> str:
        self.build_operations_prompt(prompt_type, context)
        return lead
