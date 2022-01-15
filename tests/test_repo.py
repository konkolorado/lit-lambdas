import random
import typing as t
import uuid

import arrow

from lit_lambdas.api.config import Settings
from lit_lambdas.api.models import Action, ActionStatus
from lit_lambdas.api.repository import ActionRepository


def generate_actions(
    n: t.Optional[int] = None,
    *,
    created_by: t.Optional[uuid.UUID] = None,
    status: t.Optional[ActionStatus] = None,
    randomize_created_at: bool = False,
    randomize_completed_at: bool = False,
    generate_expired: bool = False,
) -> t.List[Action]:
    if n is None:
        n = random.randint(1, 2)

    actions = []
    for _ in range(n):
        optional_kwargs = {}
        if created_by is None:
            created_by = uuid.uuid4()
        if status is None:
            status = random.choice(list(ActionStatus))
        if randomize_created_at:
            settings = Settings()
            if generate_expired:
                random_seconds = random.randint(
                    -settings.dynamo_item_ttl_s * 3, -settings.dynamo_item_ttl_s - 1
                )
            else:
                random_seconds = random.randint(0, settings.dynamo_item_ttl_s)
            rand_datetime = arrow.utcnow().shift(seconds=random_seconds).datetime
            optional_kwargs["created_at"] = rand_datetime
        if randomize_completed_at:
            random_months = random.randint(-12, 12)
            rand_datetime = arrow.utcnow().shift(months=random_months).datetime
            optional_kwargs["completed_at"] = rand_datetime

        a = Action(
            details={"endpoint": "run"},
            created_by=created_by,
            status=status,
            **optional_kwargs,
        )
        actions.append(a)
    return actions


def store_actions(repo: ActionRepository, *actions: Action):
    repo.store_actions(*actions)


def test_can_retrieve_action_by_id(repo: ActionRepository):
    actions = generate_actions()
    store_actions(repo, *actions)
    action = random.choice(actions)

    result = repo.get_action_by_id(str(action.created_by), str(action.id))
    assert result == action


def test_retrieving_by_non_existant_action(repo: ActionRepository):
    action, *_ = generate_actions()
    result = repo.get_action_by_id(str(action.created_by), str(action.id))
    assert result is None


def test_retrieving_by_non_existant_user(repo: ActionRepository):
    action, *_ = generate_actions()
    store_actions(repo, action)
    result = repo.get_action_by_id(str(uuid.uuid4()), str(action.id))
    assert result is None


def test_enumerating_user_actions(repo: ActionRepository):
    test_user_id = uuid.UUID(int=0)
    actions = generate_actions(created_by=test_user_id)
    store_actions(repo, *actions)

    result = repo.enumerate_actions_for_user(str(test_user_id))

    action_ids = set(a.id for a in actions)
    result_ids = set(r.id for r in result)
    assert result_ids == action_ids


def test_enumerating_user_actions_where_no_actions_exist(repo: ActionRepository):
    test_user_id = uuid.UUID(int=0)
    result = repo.enumerate_actions_for_user(str(test_user_id))

    assert len(result) == 0


def test_get_action_by_status(repo: ActionRepository):
    test_user_id = uuid.UUID(int=0)
    actions = generate_actions(created_by=test_user_id)
    store_actions(repo, *actions)

    status = random.choice(actions).status
    result = repo.get_actions_by_status(str(test_user_id), status)

    action_ids = set(a.id for a in actions if a.status == status)
    result_ids = set(r.id for r in result)
    assert result_ids == action_ids


def test_get_action_by_created_at_without_bounds(repo: ActionRepository):
    test_user_id = uuid.UUID(int=0)
    actions = generate_actions(created_by=test_user_id, randomize_created_at=True)
    store_actions(repo, *actions)

    result = repo.get_actions_by_created_at(str(test_user_id))

    action_ids = set(a.id for a in actions)
    result_ids = set(r.id for r in result)
    assert result_ids == action_ids


def test_get_action_by_created_at_with_bounded_since(repo: ActionRepository):
    test_user_id = uuid.UUID(int=0)
    actions = generate_actions(created_by=test_user_id, randomize_created_at=True)
    store_actions(repo, *actions)

    since = random.choice(actions).created_at
    result = repo.get_actions_by_created_at(str(test_user_id), since=since)

    action_ids = set(a.id for a in actions if a.created_at >= since)
    result_ids = set(r.id for r in result)
    assert result_ids == action_ids


def test_get_action_by_created_at_with_bounded_until(repo: ActionRepository):
    test_user_id = uuid.UUID(int=0)
    actions = generate_actions(created_by=test_user_id, randomize_created_at=True)
    store_actions(repo, *actions)

    until = random.choice(actions).created_at
    result = repo.get_actions_by_created_at(str(test_user_id), until=until)

    action_ids = set(a.id for a in actions if a.created_at <= until)
    result_ids = set(r.id for r in result)
    assert result_ids == action_ids


def test_get_action_by_created_at_with_bounds(repo: ActionRepository):
    test_user_id = uuid.UUID(int=0)
    actions = generate_actions(created_by=test_user_id, randomize_created_at=True)
    store_actions(repo, *actions)

    c1 = random.choice(actions).created_at
    c2 = random.choice(actions).created_at
    since, until = (c1, c2) if c1 < c2 else (c2, c1)
    result = repo.get_actions_by_created_at(str(test_user_id), since=since, until=until)

    action_ids = set(
        a.id for a in actions if a.created_at >= since and a.created_at <= until
    )
    result_ids = set(r.id for r in result)
    assert result_ids == action_ids


def test_get_action_by_completed_at_without_bounds(repo: ActionRepository):
    test_user_id = uuid.UUID(int=0)
    actions = generate_actions(created_by=test_user_id, randomize_completed_at=True)
    store_actions(repo, *actions)

    result = repo.get_actions_by_completed_at(str(test_user_id))

    action_ids = set(a.id for a in actions)
    result_ids = set(r.id for r in result)
    assert result_ids == action_ids


def test_get_action_by_completed_at_with_bounded_since(repo: ActionRepository):
    test_user_id = uuid.UUID(int=0)
    actions = generate_actions(created_by=test_user_id, randomize_completed_at=True)
    store_actions(repo, *actions)

    since = random.choice(actions).created_at
    result = repo.get_actions_by_completed_at(str(test_user_id), since=since)

    action_ids = set(a.id for a in actions if a.completed_at >= since)
    result_ids = set(r.id for r in result)
    assert result_ids == action_ids


def test_get_action_by_completed_at_with_bounded_until(repo: ActionRepository):
    test_user_id = uuid.UUID(int=0)
    actions = generate_actions(created_by=test_user_id, randomize_completed_at=True)
    store_actions(repo, *actions)

    until = random.choice(actions).created_at
    result = repo.get_actions_by_completed_at(str(test_user_id), until=until)

    action_ids = set(a.id for a in actions if a.completed_at <= until)
    result_ids = set(r.id for r in result)
    assert result_ids == action_ids


def test_get_action_by_completed_at_with_bounds(repo: ActionRepository):
    test_user_id = uuid.UUID(int=0)
    actions = generate_actions(created_by=test_user_id, randomize_completed_at=True)
    store_actions(repo, *actions)

    c1 = random.choice(actions).completed_at
    c2 = random.choice(actions).completed_at
    since, until = (c1, c2) if c1 < c2 else (c2, c1)
    result = repo.get_actions_by_completed_at(
        str(test_user_id), since=since, until=until
    )

    action_ids = set(
        a.id for a in actions if a.completed_at >= since and a.completed_at <= until
    )
    result_ids = set(r.id for r in result)
    assert result_ids == action_ids


def test_expired_items_are_not_returned(repo: ActionRepository):
    test_user_id = uuid.UUID(int=0)
    actions = generate_actions(
        created_by=test_user_id, randomize_created_at=True, generate_expired=True
    )
    store_actions(repo, *actions)

    result = repo.get_actions_by_completed_at(str(test_user_id))
    assert len(result) == 0

    result = repo.get_action_by_id(str(test_user_id), actions[0].id)
    assert result is None

    result = repo.get_actions_by_created_at(str(test_user_id))
    assert len(result) == 0

    status = random.choice(actions).status
    result = repo.get_actions_by_status(str(test_user_id), status)
    assert len(result) == 0

    result = repo.enumerate_actions_for_user(str(test_user_id))
    assert len(result) == 0
