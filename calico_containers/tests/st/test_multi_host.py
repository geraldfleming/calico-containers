from test_base import TestBase
from time import sleep
from sh import ErrorReturnCode, ErrorReturnCode_1
from docker_host import DockerHost


class MultiHostMainline(TestBase):
    def test_multi_host(self):
        """
        Run a mainline multi-host test. Almost identical in function to the vagrant coreOS demo.
        """
        host1 = DockerHost('host1')
        host2 = DockerHost('host2')

        calicoctl = "/code/dist/calicoctl %s"

        host1.execute(calicoctl % "reset || true")

        host1.execute(calicoctl % ("node --ip=%s" % host1.ip))
        host2.execute(calicoctl % ("node --ip=%s" % host2.ip))

        # Wait for powerstrip to come up.
        for i in range(5):
            try:
                host1.execute("docker ps", docker_host=True)
                break
            except ErrorReturnCode:
                if i == 4:
                    raise AssertionError("Powerstrip failed to come up.")
                else:
                    sleep(1)

        host1.execute("docker run -e CALICO_IP=192.168.1.1 --name workload-A -tid busybox", docker_host=True)
        host1.execute("docker run -e CALICO_IP=192.168.1.2 --name workload-B -tid busybox", docker_host=True)
        host1.execute("docker run -e CALICO_IP=192.168.1.3 --name workload-C -tid busybox", docker_host=True)

        # Wait for powerstrip to come up.
        for i in range(5):
            try:
                host2.execute("docker ps", docker_host=True)
                break
            except ErrorReturnCode:
                if i == 4:
                    raise AssertionError("Powerstrip failed to come up.")
                else:
                    sleep(1)

        host2.execute("docker run -e CALICO_IP=192.168.1.4 --name workload-D -tid busybox", docker_host=True)
        host2.execute("docker run -e CALICO_IP=192.168.1.5 --name workload-E -tid busybox", docker_host=True)

        host1.execute(calicoctl % "profile add PROF_A_C_E")
        host1.execute(calicoctl % "profile add PROF_B")
        host1.execute(calicoctl % "profile add PROF_D")

        host1.execute(calicoctl % "profile PROF_A_C_E member add workload-A")
        host1.execute(calicoctl % "profile PROF_B member add workload-B")
        host1.execute(calicoctl % "profile PROF_A_C_E member add workload-C")

        host2.execute(calicoctl % "profile PROF_D member add workload-D")
        host2.execute(calicoctl % "profile PROF_A_C_E member add workload-E")

        # Wait for the workload networking to converge.
        sleep(1)

        host1.execute("docker exec workload-A ping -c 4 192.168.1.3")

        try:
            host1.execute("docker exec workload-A ping -c 4 192.168.1.2")
            raise
        except ErrorReturnCode_1:
            pass

        try:
            host1.execute("docker exec workload-A ping -c 4 192.168.1.4")
            raise
        except ErrorReturnCode_1:
            pass

        host1.execute("docker exec workload-A ping -c 4 192.168.1.5")
