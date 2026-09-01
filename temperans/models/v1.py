import pickle
from pathlib import Path

import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

from temperans.behavior import BehaviorResult


MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"


class TemperansV1BehavioralPerception:

    def __init__(self):
        model_dir = Path(__file__).parent

        primitive_path = (
            model_dir / "temperans_v1_primitive_head.pkl"
        )

        match_path = (
            model_dir / "temperans_v1_match_head.pkl"
        )

        print("Loading Temperans V1...")

        self.tokenizer = AutoTokenizer.from_pretrained(
            MODEL_NAME
        )

        self.model = AutoModelForCausalLM.from_pretrained(
            MODEL_NAME
        )

        self.model.eval()

        self.device = torch.device(
            "mps"
            if torch.backends.mps.is_available()
            else "cpu"
        )

        self.model.to(self.device)

        with open(primitive_path, "rb") as f:
            self.primitive_head = pickle.load(f)

        with open(match_path, "rb") as f:
            self.match_head = pickle.load(f)

        print(
            "Temperans V1 ready:",
            self.device,
        )

    @torch.no_grad()
    def _pair_embedding(
        self,
        previous: str,
        current: str,
    ):
        # IMPORTANT:
        # Keep this representation identical to
        # train_temperans_v1.py.

        prev_ids = self.tokenizer(
            "PREVIOUS:\n"
            + previous
            + "\n\nCURRENT:\n",
            add_special_tokens=False,
        )["input_ids"]

        cur_ids = self.tokenizer(
            current,
            add_special_tokens=False,
        )["input_ids"]

        cur_ids = cur_ids[-256:]

        budget = max(
            1,
            768 - len(cur_ids),
        )

        prev_ids = prev_ids[-budget:]

        ids = prev_ids + cur_ids

        input_ids = torch.tensor(
            [ids],
            dtype=torch.long,
            device=self.device,
        )

        mask = torch.ones_like(input_ids)

        out = self.model(
            input_ids=input_ids,
            attention_mask=mask,
            output_hidden_states=True,
            use_cache=False,
        )

        hidden = out.hidden_states[-1][0]

        split = len(prev_ids)

        h_history = hidden[:split].mean(dim=0)
        h_current = hidden[split:].mean(dim=0)

        feature = torch.cat([
            h_current,
            h_history,
            h_current - h_history,
            h_current * h_history,
        ])

        return (
            feature
            .cpu()
            .numpy()
            .astype("float32")
        )

    def perceive(
        self,
        previous_text: str,
        current_text: str,
    ) -> BehaviorResult:

        feature = self._pair_embedding(
            previous_text,
            current_text,
        ).reshape(1, -1)

        primitive = self.primitive_head.predict(
            feature
        )[0]

        probabilities = (
            self.primitive_head.predict_proba(
                feature
            )[0]
        )

        confidence = float(
            np.max(probabilities)
        )

        match_probabilities = (
            self.match_head.predict_proba(
                feature
            )[0]
        )

        classes = list(
            self.match_head.classes_
        )

        positive_index = classes.index(1.0)

        history_match = float(
            match_probabilities[
                positive_index
            ]
        )

        result = BehaviorResult(
    primitive=str(primitive),
    confidence=confidence,
    history_conditioned=True,
    history_match=history_match,
    model_version="temperans-v1",
)

        # Add runtime diagnostic without changing
        # the frozen BehaviorResult schema yet.
        result.history_match = history_match

        return result
