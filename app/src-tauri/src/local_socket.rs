//! What the core's sockets for the worker share (`extensions::tokens`, `agent_streams`): a
//! TCP listener on loopback only, and a random secret for the run, both handed to the worker
//! in its environment and never to a coding agent (`APP_KEYS` in
//! `agent/acp_client/environment.py`).
//!
//! Loopback TCP rather than a Unix socket so the same code runs on Windows, where neither
//! Rust's std/tokio nor Python's asyncio offer Unix sockets. Any local process can connect,
//! so the secret is the gate: nothing is read or answered before it matches.

use base64::Engine;
use base64::engine::general_purpose::URL_SAFE_NO_PAD;

use crate::error::{Error, Result};

/// A listener on `127.0.0.1` at a port the OS picked, in non-blocking mode.
pub struct PrivateSocket {
    /// `127.0.0.1:<port>`, what the worker connects to.
    pub address: String,
    pub listener: std::net::TcpListener,
}

/// Binds a fresh loopback port.
pub fn bind() -> Result<PrivateSocket> {
    let listener = std::net::TcpListener::bind((std::net::Ipv4Addr::LOCALHOST, 0))?;
    listener.set_nonblocking(true)?;
    let address = listener.local_addr()?.to_string();
    Ok(PrivateSocket { address, listener })
}

/// A random secret for the run.
pub fn secret() -> Result<String> {
    let mut bytes = [0u8; 32];
    getrandom::fill(&mut bytes)
        .map_err(|e| Error::Invalid(format!("Couldn't make a secret for the worker: {e}")))?;
    Ok(URL_SAFE_NO_PAD.encode(bytes))
}

/// Compares in time that doesn't depend on where they differ.
pub fn same(a: &str, b: &str) -> bool {
    a.len() == b.len()
        && a.bytes()
            .zip(b.bytes())
            .fold(0u8, |acc, (x, y)| acc | (x ^ y))
            == 0
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn binds_loopback_only() {
        let socket = bind().unwrap();
        assert!(socket.address.starts_with("127.0.0.1:"));
        assert!(!socket.address.ends_with(":0"));
    }
}
