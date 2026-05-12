from pydantic import BaseModel, field_validator


class VoteIn(BaseModel):
    value: int      # must be +1 or -1

    @field_validator("value")
    @classmethod
    def must_be_valid(cls, v: int) -> int:
        if v not in (1, -1):
            raise ValueError("vote value must be 1 (upvote) or -1 (downvote)")
        return v


class VoteOut(BaseModel):
    vote_score: int
    upvote_count: int
    downvote_count: int
    user_vote: int      # the current user's vote after the operation