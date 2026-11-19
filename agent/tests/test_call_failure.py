import asyncio
import logging

from livekit.agents import CloseEvent, CloseReason
from livekit.agents.llm import RealtimeModelError

from call_failure import (
    ATTRIBUTE,
    LINE_CHARS,
    LIVEKIT_LOGGER,
    RECENT_S,
    ServiceErrors,
    failure_line,
    out_of_quota,
    report,
)

NO_CREDITS = (
    "You have no credits remaining. Add credits to continue using the API at "
    "https://platform.openai.com/settings/organization/billing/."
)


def logged(errors: ServiceErrors, body: object, at: float = 100.0) -> None:
    """A record as LiveKit's GPT-Live engine logs the service's error."""
    record = logging.LogRecord(
        LIVEKIT_LOGGER,
        logging.ERROR,
        __file__,
        1,
        "gpt-live returned an error",
        (),
        None,
    )
    record.created = at
    setattr(record, "lk.pii.error", body)
    assert errors.filter(record) is True


def test_the_services_own_words_are_kept_while_theyre_recent() -> None:
    errors = ServiceErrors()
    assert errors.said(now=100.0) is None

    logged(errors, {"type": "invalid_request_error", "message": NO_CREDITS})

    assert errors.said(now=100.0 + RECENT_S) == NO_CREDITS
    # An older error is some other trouble's, not why the call ended now.
    assert errors.said(now=100.0 + RECENT_S + 1) is None


def test_a_record_without_a_message_changes_nothing() -> None:
    errors = ServiceErrors()
    logged(errors, {"message": NO_CREDITS})
    for body in (None, "oops", {"code": "x"}, {"message": "  "}, {"message": 3}):
        logged(errors, body)

    assert errors.said(now=100.0) == NO_CREDITS


def test_the_line_says_who_ended_the_call_and_why() -> None:
    assert failure_line("OpenAI", NO_CREDITS) == f"OpenAI ended the call: {NO_CREDITS}"
    plain = failure_line("Gemini", None)
    assert plain.startswith("Gemini ended the call. ")
    assert "Gemini" in plain.split(". ", 1)[1]
    long = failure_line("Rime", "x" * 1000)
    assert len(long) == LINE_CHARS and long.endswith("…")


def test_only_a_session_closed_by_an_error_is_reported() -> None:
    async def scenario(reason: CloseReason) -> list[dict[str, str]]:
        published: list[dict[str, str]] = []

        async def publish(attributes: dict[str, str]) -> None:
            published.append(attributes)

        errors = ServiceErrors()
        logged(errors, {"message": NO_CREDITS})
        report(CloseEvent(reason=reason), "OpenAI", errors, publish, now=100.0)
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        return published

    assert asyncio.run(scenario(CloseReason.ERROR)) == [
        {ATTRIBUTE: f"OpenAI ended the call: {NO_CREDITS}"}
    ]
    for reason in (CloseReason.USER_INITIATED, CloseReason.PARTICIPANT_DISCONNECTED):
        assert asyncio.run(scenario(reason)) == []


def closed_on(error: Exception, reason: CloseReason = CloseReason.ERROR) -> CloseEvent:
    return CloseEvent(
        reason=reason,
        error=RealtimeModelError(
            timestamp=0.0, label="gemini", error=error, recoverable=False
        ),
    )


def test_sees_a_quota_running_out_in_the_errors_cause() -> None:
    # As Gemini's plugin raises it: its own error, caused by the service's 1011.
    try:
        try:
            raise RuntimeError(
                "1011 None. You exceeded your current quota, please check your plan"
            )
        except RuntimeError as cause:
            raise ConnectionError("Failed to connect to Gemini Live") from cause
    except ConnectionError as error:
        assert out_of_quota(closed_on(error))
        assert not out_of_quota(closed_on(error, CloseReason.USER_INITIATED))


def test_other_failures_arent_quota() -> None:
    assert not out_of_quota(closed_on(RuntimeError("1008 API key not valid")))
    assert not out_of_quota(CloseEvent(reason=CloseReason.ERROR))
