"""Lifecycle nodes を configure/activate までリトライ付きで進める。"""

from __future__ import annotations

import threading
import time
from typing import Iterable

import rclpy
from lifecycle_msgs.msg import State
from lifecycle_msgs.msg import Transition
from lifecycle_msgs.srv import ChangeState
from lifecycle_msgs.srv import GetState
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node


class LifecycleBringupRetry(Node):
    """Nav2 lifecycle manager の代わりに、状態遷移を地道にリトライする。"""

    def __init__(self) -> None:
        super().__init__("lifecycle_bringup_retry")
        # Empty list is inferred as BYTE_ARRAY on Humble, so seed with strings.
        self.declare_parameter("node_names", ["map_server", "amcl"])
        self.declare_parameter("target_namespace", "")
        self.declare_parameter("retry_count", 20)
        self.declare_parameter("service_wait_sec", 2.0)
        self.declare_parameter("retry_delay_sec", 1.0)
        self.declare_parameter("startup_delay_sec", 3.0)

        self.node_names = [str(name) for name in self.get_parameter("node_names").value]
        self.target_namespace = str(self.get_parameter("target_namespace").value).strip()
        self.retry_count = int(self.get_parameter("retry_count").value)
        self.service_wait_sec = float(self.get_parameter("service_wait_sec").value)
        self.retry_delay_sec = float(self.get_parameter("retry_delay_sec").value)
        self.startup_delay_sec = float(self.get_parameter("startup_delay_sec").value)

        self.timer = self.create_timer(self.startup_delay_sec, self.run_once)
        self.completed = False

    def run_once(self) -> None:
        if self.completed:
            return
        self.completed = True
        self.timer.cancel()

        threading.Thread(target=self._bringup_worker, daemon=True).start()

    def _bringup_worker(self) -> None:
        ok = self.bringup_nodes(self.node_names)
        if ok:
            self.get_logger().info("Lifecycle bringup completed.")
        else:
            self.get_logger().error("Lifecycle bringup failed.")

    def bringup_nodes(self, node_names: Iterable[str]) -> bool:
        for node_name in node_names:
            current_state = self.get_current_state(node_name)
            if current_state is None:
                return False

            if current_state == State.PRIMARY_STATE_ACTIVE:
                self.get_logger().info(f"{node_name} is already active.")
                continue

            if current_state == State.PRIMARY_STATE_UNCONFIGURED:
                if not self.change_state_with_retry(
                    node_name, Transition.TRANSITION_CONFIGURE, "configure"
                ):
                    return False
                current_state = self.get_current_state(node_name)
                if current_state is None:
                    return False

            if current_state == State.PRIMARY_STATE_INACTIVE:
                if not self.change_state_with_retry(
                    node_name, Transition.TRANSITION_ACTIVATE, "activate"
                ):
                    return False
                current_state = self.get_current_state(node_name)
                if current_state is None:
                    return False

            if current_state != State.PRIMARY_STATE_ACTIVE:
                self.get_logger().error(
                    f"{node_name} ended in unexpected state {current_state}."
                )
                return False
        return True

    def scoped_service_name(self, node_name: str, service_name: str) -> str:
        namespace = self.target_namespace
        if namespace and not namespace.startswith("/"):
            namespace = "/" + namespace
        if namespace.endswith("/"):
            namespace = namespace[:-1]
        if namespace:
            return f"{namespace}/{node_name}/{service_name}"
        return f"/{node_name}/{service_name}"

    def wait_for_state(self, node_name: str, target_state: int) -> bool:
        state = self.get_current_state(node_name)
        if state is None:
            return False
        return state == target_state

    def get_current_state(self, node_name: str) -> int | None:
        service_name = self.scoped_service_name(node_name, "get_state")
        client = self.create_client(GetState, service_name)
        for attempt in range(1, self.retry_count + 1):
            if not client.wait_for_service(timeout_sec=self.service_wait_sec):
                self.get_logger().warn(
                    f"Service not ready yet: {service_name} "
                    f"(attempt {attempt}/{self.retry_count})."
                )
                time.sleep(self.retry_delay_sec)
                continue

            request = GetState.Request()
            future = client.call_async(request)
            if self.wait_for_future(future, self.service_wait_sec) and future.result() is not None:
                current_id = future.result().current_state.id
                current_label = future.result().current_state.label
                self.get_logger().info(
                    f"{node_name} currently '{current_label}' ({current_id})."
                )
                return current_id
            else:
                self.get_logger().warn(
                    f"{service_name} timed out "
                    f"(attempt {attempt}/{self.retry_count})."
                )
            time.sleep(self.retry_delay_sec)

        self.get_logger().error(f"{node_name} state could not be read.")
        return None

    def change_state_with_retry(
        self, node_name: str, transition_id: int, transition_name: str
    ) -> bool:
        service_name = self.scoped_service_name(node_name, "change_state")
        client = self.create_client(ChangeState, service_name)
        for attempt in range(1, self.retry_count + 1):
            if not client.wait_for_service(timeout_sec=self.service_wait_sec):
                self.get_logger().warn(
                    f"Service not ready yet: {service_name} "
                    f"(attempt {attempt}/{self.retry_count})."
                )
                time.sleep(self.retry_delay_sec)
                continue

            request = ChangeState.Request()
            request.transition.id = transition_id
            future = client.call_async(request)
            if (
                self.wait_for_future(future, self.service_wait_sec)
                and future.result() is not None
                and future.result().success
            ):
                self.get_logger().info(
                    f"{node_name} {transition_name} succeeded "
                    f"(attempt {attempt}/{self.retry_count})."
                )
                return True

            self.get_logger().warn(
                f"{node_name} {transition_name} did not complete "
                f"(attempt {attempt}/{self.retry_count})."
            )
            time.sleep(self.retry_delay_sec)

        self.get_logger().error(
            f"{node_name} failed to {transition_name} after {self.retry_count} attempts."
        )
        return False

    def wait_for_future(self, future, timeout_sec: float) -> bool:
        deadline = time.monotonic() + timeout_sec
        while time.monotonic() < deadline:
            if future.done():
                return True
            time.sleep(0.05)
        return future.done()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = LifecycleBringupRetry()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
