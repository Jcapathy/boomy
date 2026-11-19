//! Waiting on the programs the core runs (agents' `--version`, adapter installs, the voice
//! agent). std has no `Child::wait_timeout` as of Rust 1.99, so this polls `try_wait`.

use std::io;
#[cfg(windows)]
use std::process::Stdio;
use std::process::{Child, Command, ExitStatus};
use std::thread;
use std::time::{Duration, Instant};

const TICK: Duration = Duration::from_millis(50);

/// Waits up to `timeout` for `child` to exit: its status, or `None` if it's still running.
pub fn wait_timeout(child: &mut Child, timeout: Duration) -> io::Result<Option<ExitStatus>> {
    let started = Instant::now();
    loop {
        if let Some(status) = child.try_wait()? {
            return Ok(Some(status));
        }
        if started.elapsed() >= timeout {
            return Ok(None);
        }
        thread::sleep(TICK);
    }
}

/// Windows' `CREATE_NO_WINDOW`: a console program started from the app (a GUI program)
/// otherwise opens a console window of its own.
#[cfg(windows)]
pub const CREATE_NO_WINDOW: u32 = 0x0800_0000;

/// Starts `command` so [`stop_group`] can stop it with everything it starts: in a process
/// group of its own on Unix. On Windows, which stops a tree by parent pid instead, only
/// without a console window.
pub fn own_group(command: &mut Command) {
    #[cfg(unix)]
    std::os::unix::process::CommandExt::process_group(command, 0);
    #[cfg(windows)]
    no_window(command);
}

/// No console window for `command` on Windows; nothing elsewhere.
pub fn no_window(command: &mut Command) {
    #[cfg(windows)]
    std::os::windows::process::CommandExt::creation_flags(command, CREATE_NO_WINDOW);
    #[cfg(not(windows))]
    let _ = command;
}

/// Ends `pid` and every process it started, by force: Windows has no process groups to
/// signal, and console programs without a window take no polite close.
#[cfg(windows)]
pub fn kill_tree(pid: u32) {
    let mut taskkill = Command::new("taskkill");
    taskkill
        .args(["/T", "/F", "/PID", &pid.to_string()])
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::null());
    no_window(&mut taskkill);
    let _ = taskkill.status();
}

/// For a child that leads its process group (started with [`own_group`], or in a session of
/// its own): SIGTERM to its group, SIGKILL after `grace`. On Windows, its whole tree at once.
pub fn stop_group(mut child: Child, grace: Duration) {
    #[cfg(unix)]
    if let Ok(pid) = i32::try_from(child.id()) {
        // SAFETY: killpg only sends a signal; the group is the one the child leads.
        unsafe { libc::killpg(pid, libc::SIGTERM) };
        if let Ok(Some(_)) = wait_timeout(&mut child, grace) {
            return;
        }
        unsafe { libc::killpg(pid, libc::SIGKILL) };
    }
    #[cfg(windows)]
    {
        let _ = grace;
        kill_tree(child.id());
    }
    kill(&mut child);
}

/// Kills `child` and reaps it, so it leaves no zombie.
pub fn kill(child: &mut Child) {
    let _ = child.kill();
    let _ = child.wait();
}

#[cfg(test)]
mod tests {
    use std::process::Command;

    use super::*;

    /// A program that exits at once, and one that runs for about 5 s.
    #[cfg(unix)]
    fn programs() -> (Command, Command) {
        let mut sleep = Command::new("sleep");
        sleep.arg("5");
        (Command::new("true"), sleep)
    }

    #[cfg(windows)]
    fn programs() -> (Command, Command) {
        let mut exits = Command::new("cmd");
        exits.args(["/C", "exit 0"]);
        let mut sleep = Command::new("ping");
        sleep.args(["-n", "6", "127.0.0.1"]).stdout(Stdio::null());
        (exits, sleep)
    }

    #[test]
    fn returns_the_status_of_a_program_that_exits() {
        let mut child = programs().0.spawn().unwrap();
        let status = wait_timeout(&mut child, Duration::from_secs(5)).unwrap();
        assert!(status.is_some_and(|s| s.success()));
    }

    #[test]
    fn gives_up_on_a_program_that_keeps_running() {
        let mut child = programs().1.spawn().unwrap();
        let status = wait_timeout(&mut child, Duration::from_millis(100)).unwrap();
        assert!(status.is_none());
        kill(&mut child);
    }

    #[cfg(windows)]
    #[test]
    fn stop_group_ends_what_the_child_started() {
        // cmd starts a ping of its own; stopping cmd must take the ping with it.
        let mut parent = Command::new("cmd");
        parent
            .args(["/C", "ping -n 30 127.0.0.1 > NUL"])
            .stdout(Stdio::null());
        let child = parent.spawn().unwrap();
        let pid = child.id();
        std::thread::sleep(Duration::from_millis(500));
        stop_group(child, Duration::from_secs(1));
        let out = Command::new("powershell")
            .args([
                "-NoProfile",
                "-Command",
                &format!("@(Get-CimInstance Win32_Process -Filter 'ParentProcessId={pid}').Count"),
            ])
            .output()
            .unwrap();
        assert_eq!(
            String::from_utf8_lossy(&out.stdout).trim(),
            "0",
            "a child outlived it"
        );
    }
}
