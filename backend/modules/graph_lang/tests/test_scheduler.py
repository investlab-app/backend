import pytest
from unittest.mock import patch
from modules.graph_lang.framework.scheduler import Scheduler, SchedulerGraph
from modules.graph_lang.framework.nodes import CheckEveryNode
from datetime import timedelta, datetime

class MockRunner:
    def __init__(self):
        self.ran_graphs = []

    def run(self, id :str):
        self.ran_graphs.append(id)

    def get_ran_graphs(self) -> list[str]:
        return self.ran_graphs

class MockSchedulerProvider:
    def __init__(self):
        self.graphs = {}

    def get_graph(self, id :str) -> SchedulerGraph:
        return self.graphs[id]

    def set_graph(self, graph :SchedulerGraph):
        self.graphs[graph.id] = graph

    def remove_graph(self, id :str):
        self.graphs.pop(id)

class MockDateTime:
    def __init__(self):
        self._now = datetime.now()

    def now(self):
        return self._now

    def skip_time(self, td :timedelta):
        self._now += td


class TestSchedulerBase:
    @pytest.fixture(autouse=True)
    def setup(self, datetime_mock):
        self.datetime = datetime_mock
        self.runner = MockRunner()
        self.provider = MockSchedulerProvider()
        self.scheduler = Scheduler(self.runner, self.provider,
                                   max_sleep_timespan=timedelta(days=30))

    @pytest.fixture()
    def datetime_mock(self):
        with patch('modules.graph_lang.framework.scheduler.datetime', new_callable=MockDateTime) as mock:
            yield mock

    def add_timer_node(self, id, td, investor_id = '1'):
        node = CheckEveryNode()
        node.timespan.set(td)
        graph = SchedulerGraph(
            id=id,
            investor_id=investor_id,
            trigger = node
        )
        self.provider.set_graph(graph)
        self.scheduler.add_graph(id)

    def skip_days(self, days):
        self.datetime.skip_time(timedelta(days=days))
        self.scheduler.step()

    def skip_hours(self, hours):
        self.datetime.skip_time(timedelta(hours=hours))
        self.scheduler.step()



class TestScheduler(TestSchedulerBase):
    def test_no_graph__no_graph_is_ran(self):
        self.scheduler.step()

        assert self.runner.get_ran_graphs() == []

    def test_remove_graph__invalid_id_passed__gets_ignored(self):
        self.scheduler.remove_graph('test')

    def test_add_graph__graph_does_not_exist__gets_ignored(self):
        self.scheduler.add_graph('test')

    def test_update_graph__graph_does_not_exist__gets_ignored(self):
        self.scheduler.add_graph('test')


class TestMultipleTimersScheduler(TestSchedulerBase):
    @pytest.fixture(autouse=True)
    def setup_multiple_timer(self):
        self.add_timer_node(id='1', td = timedelta(days=3))
        self.add_timer_node(id='2', td = timedelta(days=4))
        self.add_timer_node(id='3', td = timedelta(days=2))

    def test_multiple_timer_graphs__max_sleep_is_earliest_timedelta(self):
        max_sleep = self.scheduler.get_max_idle_datetime()
        expected = self.datetime.now() + timedelta(days=2)

        assert max_sleep == expected

    def test_multiple_timer_graphs__skip_time__some_graphs_are_ran(self):
        self.skip_days(3)

        assert self.runner.get_ran_graphs() == ['1', '3']


class TestSingleTimerScheduler(TestSchedulerBase):
    @pytest.fixture(autouse=True)
    def setup_single_timer(self):
        self.add_timer_node(id='1', td = timedelta(days=1))

    def test_single_timer_graph__no_step__no_graph_ran(self):
        self.scheduler.step()
        assert self.runner.get_ran_graphs() == []

    def test_single_timer_graph__max_sleep_equals_timedelta(self):
        max_sleep = self.scheduler.get_max_idle_datetime()
        assert max_sleep == self.datetime.now() + timedelta(days=1)


    def test_default_max_is_biggest_sleep__max_sleep_is_default(self):
        self.scheduler.max_sleep_timespan = timedelta(days=1)

        max_sleep = self.scheduler.get_max_idle_datetime()
        assert max_sleep == (self.datetime.now() + timedelta(days=1))

    def test_single_timer_graph__after_specified_time__is_ran(self):
        self.skip_days(1)

        assert self.runner.get_ran_graphs() == ['1']

    def test_single_timer_graph__graph_is_ran__multiple_times(self):
        for _ in range(4):
            self.skip_hours(12)

        assert self.runner.get_ran_graphs() == ['1', '1']

    def test__graph_is_deleted__no_graph_is_ran(self):
        self.scheduler.remove_graph('1')
        self.skip_days(1)

        assert self.runner.get_ran_graphs() == []

    def test__graph_is_updated__timer_gets_reset(self):
        self.skip_hours(12)
        self.add_timer_node('1', timedelta(days=1, hours=1))
        self.scheduler.update_graph('1')

        self.skip_days(1)
        assert self.runner.get_ran_graphs() == []
        self.skip_hours(1)
        assert self.runner.get_ran_graphs() == ['1']



