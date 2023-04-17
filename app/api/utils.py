def determine_vote_weight(votes_weights: list[float], vote_num: int, default_weight: float = 1.0) -> float:
    if not votes_weights:
        return default_weight

    if vote_num == 0:
        return votes_weights[0]
    elif vote_num <= len(votes_weights):
        return votes_weights[vote_num - 1]
    return votes_weights[-1]
