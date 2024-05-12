import random
import subprocess
import time
import libtmux

JUMP_BOX = None  # enter your jump box ip
VM_LISTS = []  # enter a list of your vms.
PASSWORDS = []  # enter the corresponding password list for the vms.


class Connection:
    """
        this class will hold all functionality regarding tmux connections.
    """
    server = None  # a server hold all session, that holds all windows, inside each window is a pane to run cmds.

    def __init__(self):

        # Create a new server object,
        self.server = libtmux.Server()

    def __del__(self):
        self.server.kill_server()

    def create_detached_tmux_session(self, session_name="") -> libtmux.Session:
        """
        this function creates a tmux session in background.
        :param session_name: we can choose it, so we can recognize it later.
        :return: our session instance.
        """
        try:
            '''
            session name rules: we cannot havev two sessions with the same name,
            session name may not contains "." or ":" chars.
            if we do not specify a name then it is going to be random my_session#
            '''
            if session_name != "":
                # Create a new session in detached mode, using our name.
                session = self.server.new_session(session_name=session_name, detached=True)
                print(f"Detached tmux session '{session_name}' created successfully.")
                return session
            else:
                # if not specify we get random name.
                random_name = "my_session" + str(random.randint(100, 10000))
                while random_name in self.server.sessions:
                    random_name = "my_session" + str(random.randint(100, 10000))
                session = self.server.new_session(session_name=random_name, detached=True)
                print(f"Detached tmux session {random_name} created successfully.")
                return session
        except subprocess.CalledProcessError as e:
            print(f"Error creating detached tmux session: {e}")

    def is_tmux_session_running(self, session_name) -> bool:
        """
        this function gets a session name, and check to see if It's running or not.
        :return:True if it is, False otherwise.
        """
        try:
            # Check if the tmux session exists
            if session_name in self.server.sessions:
                return True
            else:
                return False
        except Exception as e:
            print(f"Something went wrong: {e}")

    def kill_session_by_name(self, session_name):
        """
        function gets session name and end it.
        :param session_name: the session we want to terminate.
        """
        try:
            # Find the session by name
            session = self.server.find_where({"session_name": session_name})
            if session:
                # Kill the session
                session.kill_session()
                print(f"tmux session '{session_name}' killed successfully.")
            else:
                print(f"No tmux session found with name '{session_name}'.")
        except Exception as e:
            print(f"could not kill session, exception: {e}")

    def run_cmd(self, command, session_name, window_name="", pane_name="") -> libtmux.pane:
        """
        function get as string a tmux command and execute it as is.
        for now its from the
        :param command: as a string.
        :param session_name: to run this command in it.
        """
        try:
            session = self.server.find_where({"session_name": session_name})
            if session is None:
                raise Exception(f"no session with name {session_name} was found.")
            if len(session.list_windows) != 0:
                window = [w for w in session.list_windows if w.name == window_name][0]  # list suppose to be len 1.
            else:
                raise Exception(f"No window with name {window_name} was found.")
            if len(window.list_panes) != 0:
                pane = [p for p in window.list_panes if p.name == pane_name][0]  # Select the first pane in the window
            else:
                raise Exception(f"No window with name {pane_name} was found.")
            result = pane.send_keys(command)
            time.sleep(2)
            print("Command executed successfully:")
            return result
        except Exception as e:
            print("Error executing command:", e)

    def run_cmd(self, pane: libtmux.pane, cmd: str) -> libtmux.pane:
        """
        this function execute a command in existing pane.
        :param pane: that we want to execute the command in.
        :param cmd: command to be executed.
        """
        try:
            pane.send_keys(cmd=cmd)
            time.sleep(2)  # let command finish.
            print("Command executed successfully:")
        except Exception as e:
            print("Error executing command:", e)

    def enter_password(selfself, pane: libtmux.pane, password: str):
        try:
            pane.send_keys(suppress_history=False, cmd=password)
        except Exception as e:
            print(f"somthing went wrong: {e}")

    # TODO: make sure this function can use any pane we wish using its name.
    def run_ssh_command_with_password(self, session_name, port, VM_IP, JB_IP, JB_username="root",
                                      JB_password="password"):
        """
        this function set a ssh tunnel between vdi and Franklin vm (via Franklin jump box).
        :param session_name: in which session to execute this command.
        :param port: to use in localhost.
        :param VM_IP: Franklin VM to connect to.
        :param JB_IP: Jump box ip
        :param JB_username: Jump box username (usually root)
        :param JB_password: TODO-> this should not be used! unsafe.
        """
        try:
            # Find the session by name
            session = self.server.find_where({"session_name": session_name})
            if session:
                # construct the cmd to run
                command = f'ssh -4 -N -L localhost:{port}:{VM_IP}:22 {JB_username}@{JB_IP}'
                # Run the SSH command within the tmux session
                window = session.select_window(0)
                pane = window.select_pane(0)
                pane.send_keys(command)
                time.sleep(2)
                # important suppress history adds " " to string if no False.
                pane.send_keys(JB_password, suppress_history=False)
                print("SSH command executed successfully")
            else:
                print(f"No tmux session found with name '{session_name}'.")
        except Exception as e:
            print("Error executing SSH command:", e)

    def create_new_pane(self, session_name, window_name="", pane_name="") -> libtmux.pane:
        """
        this function creates new pane, essentially a pane is a new terminal in the same window.
        :param session_name: in case we got several sessions.
        :param window_name: to create the pane in.
        :param pane_name: if we wish to set the pane name.
        :return: an instance of the new pane.
        """
        try:
            # first we find the session.
            session = self.server.find_where({"session_name": session_name})
            if session is None:
                raise Exception(f"no session with name {session_name} was found.")
            # we look for specific window, if there are windows, and its name is specified.
            if len(session.list_windows()) != 0 and window_name != "":
                window = [w for w in session.list_windows() if w.name == window_name][0]  # list suppose to be len 1.
            # we got windows, but we don't specify a window name.
            elif len(session.list_windows()) != 0 and window_name == "":
                window = [w for w in session.list_windows()][0]  # then we use first window in session.
            else:
                raise Exception(f"No window with name {window_name} was found.")
            if pane_name in window.list_panes():
                raise Exception(f"pane name {pane_name} already exists.")
            pane = window.split_window(attach=False)
            # pane.set_shell_command("bash --rcfile ~/.bashrc", window_name + "-pane")
            return pane  # we return the instance of our new pane.
        except Exception as e:
            print(f"an error occurred: " + str(e))

    # Example usage


if __name__ == "__main__":
    session_name = "my_session"
    try:
        my_connection = Connection()
        my_connection.create_detached_tmux_session(session_name)
        print("The sessions currently running: " + str(my_connection.server.sessions))
        for i in range(0, 4):
            pane = my_connection.create_new_pane(session_name, pane_name=f"pane#{i}")
            my_connection.run_cmd(pane,
                                  f"sshuttle -r root@{JUMP_BOX} {VM_LISTS[i]}/16 --no-latency-control")
            time.sleep(2)
            my_connection.enter_password(pane, PASSWORDS[i])
            print(f"A ssh tunnel from vdi to {VM_LISTS[i]} via {JUMP_BOX} was created.")
        input("click any-key")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        my_connection.kill_session_by_name(session_name)
