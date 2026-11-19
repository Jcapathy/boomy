// App commands listed here get `allow-<command>` permissions, and then a window can call a
// command only if one of its capabilities (capabilities/*.json) grants it. Keep this list in
// sync with generate_handler! in lib.rs.
const COMMANDS: &[&str] = &[
    "open_settings",
    "set_tray_status",
    "task_finished",
    "about",
    "check_for_updates",
    "install_update",
    "export_diagnostics",
    "show_diagnostics",
    "app_log",
    "credentials_info",
    "save_credentials",
    "clear_credentials",
    "save_voice_key",
    "clear_voice_key",
    "has_zep_key",
    "save_zep_key",
    "clear_zep_key",
    "agent_keys",
    "save_agent_key",
    "clear_agent_key",
    "read_keys_again",
    "keychain_asking",
    "memory_setting",
    "set_memory_setting",
    "memory_incognito",
    "set_memory_incognito",
    "livekit_server",
    "set_livekit_server",
    "agents_status",
    "refresh_agents",
    "agent_settings",
    "pick_agent_settings",
    "install_adapters",
    "open_call",
    "call_token",
    "end_call",
    "save_message",
    "call_transcript",
    "rename_call",
    "search",
    "delete_call",
    "voice_settings",
    "set_voice_provider",
    "set_voice",
    "set_voice_option",
    "user_name",
    "set_user_name",
    "tone",
    "set_tone",
    "first_run",
    "finish_first_run",
    "main_window_ready",
    "list_projects",
    "create_project",
    "update_project",
    "set_project_agents",
    "set_project_extensions",
    "extensions_settings",
    "set_extension",
    "connect_extension",
    "cancel_extension_connect",
    "disconnect_extension",
    "open_extension_link",
    "list_todos",
    "add_todos",
    "update_todo",
    "remove_todo",
    "delete_project",
    "folder_info",
    "folder_changes",
    "folder_entries",
    "folder_file",
    "folder_image",
    "watch_folder",
    "unwatch_folder",
    "terminal_open",
    "terminal_write",
    "terminal_resize",
    "terminal_close",
    "watch_agent_streams",
    "unwatch_agent_streams",
];

fn main() {
    let mut attributes = tauri_build::Attributes::new()
        .app_manifest(tauri_build::AppManifest::new().commands(COMMANDS));
    // Tauri embeds its Windows manifest only in the app's binary; test binaries then fail to
    // start (STATUS_ENTRYPOINT_NOT_FOUND, no Common Controls v6). Embed ours in every one.
    if std::env::var("CARGO_CFG_TARGET_OS").as_deref() == Ok("windows") {
        attributes = attributes
            .windows_attributes(tauri_build::WindowsAttributes::new_without_app_manifest());
        let manifest = std::path::Path::new(&std::env::var("CARGO_MANIFEST_DIR").unwrap())
            .join("windows-app-manifest.xml");
        println!("cargo:rerun-if-changed={}", manifest.display());
        println!("cargo:rustc-link-arg=/MANIFEST:EMBED");
        println!("cargo:rustc-link-arg=/MANIFESTINPUT:{}", manifest.display());
        println!("cargo:rustc-link-arg=/WX");
        // tauri.windows.conf.json bundles the frozen agent, and tauri-build checks every
        // resource exists on every build, even clippy and tests, which never freeze it. Debug
        // builds run the agent from source, so an empty folder stands in for them; a release
        // build still fails without the real one (`just app build` freezes it first).
        if std::env::var("PROFILE").as_deref() != Ok("release") {
            let agent = std::path::Path::new(&std::env::var("CARGO_MANIFEST_DIR").unwrap())
                .join("../../agent/dist/bomby-agent");
            std::fs::create_dir_all(agent).expect("couldn't create the agent's placeholder");
        }
    }
    tauri_build::try_build(attributes).expect("failed to run tauri-build");
}
