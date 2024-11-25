# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from __future__ import annotations

import pprint
import time
from typing import NewType, Any, Dict, List, Optional, Tuple, Union

import anki  # pylint: disable=unused-import
import anki.collection
import anki.decks
import anki.notes
import anki.template
from anki import cards_pb2, hooks
from anki._legacy import DeprecatedNamesMixin, deprecated
from anki.consts import *
from anki.models import NotetypeDict, TemplateDict
from anki.notes import Note
from anki.sound import AVTag
from anki.utils import int_time

# Cards
##########################################################################

# Type: 0=new, 1=learning, 2=due
# Queue: same as above, and:
#        -1=suspended, -2=user buried, -3=sched buried
# Due is used differently for different queues.
# - new queue: position
# - rev queue: integer day
# - lrn queue: integer timestamp

# types
CardId = NewType("CardId", int)
BackendCard = cards_pb2.Card
FSRSMemoryState = cards_pb2.FsrsMemoryState


class Card(DeprecatedNamesMixin):
    _note: Note | None
    lastIvl: int
    ord: int
    nid: anki.notes.NoteId
    id: CardId
    did: anki.decks.DeckId
    odid: anki.decks.DeckId
    queue: CardQueue
    type: CardType
    memory_state: FSRSMemoryState | None
    desired_retention: float | None
    _hint_history: List[str]
    _hints_used: int

    def __init__(
        self,
        col: anki.collection.Collection | None = None,
        id: CardId | None = None,
        backend_card: BackendCard | None = None,
    ) -> None:
        """Initialize a card with the given collection and optional ID."""
        self.col = col.weakref() if col else None
        self.timer_started: float | None = None
        self._render_output: anki.template.TemplateRenderOutput | None = None
        self.id = id
        self._hint_history: List[str] = []
        self._hints_used: int = 0
        if id:
            # existing card
            self._load_from_backend_card(self.col._backend.get_card(self.id))
            self._load_hints()
        elif backend_card:
            self._load_from_backend_card(backend_card)
        else:
            # new card with defaults
            self._load_from_backend_card(cards_pb2.Card())

    def load(self) -> None:
        card = self.col._backend.get_card(self.id)
        assert card
        self._load_from_backend_card(card)
        self._load_hints()

    def _load_from_backend_card(self, card: cards_pb2.Card) -> None:
        self._render_output = None
        self._note = None
        self.id = CardId(card.id)
        self.nid = anki.notes.NoteId(card.note_id)
        self.did = anki.decks.DeckId(card.deck_id)
        self.ord = card.template_idx
        self.mod = card.mtime_secs
        self.usn = card.usn
        self.type = CardType(card.ctype)
        self.queue = CardQueue(card.queue)
        self.due = card.due
        self.ivl = card.interval
        self.factor = card.ease_factor
        self.reps = card.reps
        self.lapses = card.lapses
        self.left = card.remaining_steps
        self.odue = card.original_due
        self.odid = anki.decks.DeckId(card.original_deck_id)
        self.flags = card.flags
        self.original_position = (
            card.original_position if card.HasField("original_position") else None
        )
        self.custom_data = card.custom_data
        self.memory_state = card.memory_state if card.HasField("memory_state") else None
        self.desired_retention = (
            card.desired_retention if card.HasField("desired_retention") else None
        )

    def _load_hints(self) -> None:
        """Load hints from the database."""
        if not self.col or not self.id:
            return
        
        hints = self.col.db.list(
            "SELECT hint FROM dory_hints WHERE cid = ? ORDER BY created ASC",
            self.id
        )
        self._hint_history = hints or []
        
        stats = self.col.db.first(
            "SELECT hints_used FROM dory_hint_stats WHERE cid = ?",
            self.id
        )
        self._hints_used = stats[0] if stats else 0

    def _to_backend_card(self) -> cards_pb2.Card:
        # mtime & usn are set by backend
        return cards_pb2.Card(
            id=self.id,
            note_id=self.nid,
            deck_id=self.did,
            template_idx=self.ord,
            ctype=self.type,
            queue=self.queue,
            due=self.due,
            interval=self.ivl,
            ease_factor=self.factor,
            reps=self.reps,
            lapses=self.lapses,
            remaining_steps=self.left,
            original_due=self.odue,
            original_deck_id=self.odid,
            flags=self.flags,
            original_position=self.original_position,
            custom_data=self.custom_data,
            memory_state=self.memory_state,
            desired_retention=self.desired_retention,
        )

    @deprecated(info="please use col.update_card()")
    def flush(self) -> None:
        hooks.card_will_flush(self)
        if self.id != 0:
            self.col._backend.update_cards(
                cards=[self._to_backend_card()], skip_undo_entry=True
            )
        else:
            raise Exception("card.flush() expects an existing card")

    def question(self, reload: bool = False, browser: bool = False) -> str:
        return self.render_output(reload, browser).question_and_style()

    def answer(self) -> str:
        return self.render_output().answer_and_style()

    def question_av_tags(self) -> list[AVTag]:
        return self.render_output().question_av_tags

    def answer_av_tags(self) -> list[AVTag]:
        return self.render_output().answer_av_tags

    def render_output(
        self, reload: bool = False, browser: bool = False
    ) -> anki.template.TemplateRenderOutput:
        if not self._render_output or reload:
            self._render_output = (
                anki.template.TemplateRenderContext.from_existing_card(
                    self, browser
                ).render()
            )
        return self._render_output

    def set_render_output(self, output: anki.template.TemplateRenderOutput) -> None:
        self._render_output = output

    def note(self, reload: bool = False) -> Note:
        if not self._note or reload:
            self._note = self.col.get_note(self.nid)
        return self._note

    def note_type(self) -> NotetypeDict:
        return self.col.models.get(self.note().mid)

    def template(self) -> TemplateDict:
        notetype = self.note_type()
        if notetype["type"] == MODEL_STD:
            return self.note_type()["tmpls"][self.ord]
        else:
            return self.note_type()["tmpls"][0]

    def start_timer(self) -> None:
        self.timer_started = time.time()

    def current_deck_id(self) -> anki.decks.DeckId:
        return anki.decks.DeckId(self.odid or self.did)

    def time_limit(self) -> int:
        "Time limit for answering in milliseconds."
        conf = self.col.decks.config_dict_for_deck_id(self.current_deck_id())
        return conf["maxTaken"] * 1000

    def should_show_timer(self) -> bool:
        conf = self.col.decks.config_dict_for_deck_id(self.current_deck_id())
        return conf["timer"]

    def replay_question_audio_on_answer_side(self) -> bool:
        conf = self.col.decks.config_dict_for_deck_id(self.current_deck_id())
        return conf.get("replayq", True)

    def autoplay(self) -> bool:
        return self.col.decks.config_dict_for_deck_id(self.current_deck_id())[
            "autoplay"
        ]

    def time_taken(self, capped: bool = True) -> int:
        """Time taken since card timer started, in integer MS.
        If `capped` is true, returned time is limited to deck preset setting."""
        total = int((time.time() - self.timer_started) * 1000)
        if capped:
            total = min(total, self.time_limit())
        return total

    def description(self) -> str:
        dict_copy = dict(self.__dict__)
        # remove non-useful elements
        del dict_copy["_note"]
        del dict_copy["_render_output"]
        del dict_copy["col"]
        del dict_copy["timer_started"]
        return f"{super().__repr__()} {pprint.pformat(dict_copy, width=300)}"

    def user_flag(self) -> int:
        return self.flags & 0b111

    def set_user_flag(self, flag: int) -> None:
        print("use col.set_user_flag_for_cards() instead")
        if not 0 <= flag <= 7:
            raise Exception("invalid flag")
        self.flags = (self.flags & ~0b111) | flag

    @deprecated(info="use card.render_output() directly")
    def css(self) -> str:
        return f"<style>{self.render_output().css}</style>"

    @deprecated(info="handled by template rendering")
    def is_empty(self) -> bool:
        return False

    def get_hints(self) -> Optional[List[str]]:
        """Get hints for this card."""
        try:
            hints = self.col.db.list("SELECT hint FROM dory_hints WHERE card_id = ? ORDER BY created_at", self.id)
            return hints if hints else None
        except Exception as e:
            return None

    def add_hint(self, hint: str) -> None:
        """Add a hint for this card."""
        try:
            self.col.db.execute(
                "INSERT INTO dory_hints (card_id, hint, created_at) VALUES (?, ?, ?)",
                self.id, hint, int_time()
            )
            self.col.db.commit()
        except Exception as e:
            pass  # Silently fail if table doesn't exist yet

    def get_hints_used(self) -> int:
        """Get the number of hints used for this card."""
        return self._hints_used

    def clear_hints(self) -> None:
        """Clear all hints for this card."""
        self._hint_history.clear()
        self._hints_used = 0
        self.mod = int_time()


Card.register_deprecated_aliases(
    flushSched=Card.flush,
    q=Card.question,
    a=Card.answer,
    model=Card.note_type,
)
