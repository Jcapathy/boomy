# Puts LiveKit's own Windows build of the server in app/src-tauri/binaries for the app to
# bundle (`just livekit build` on Windows). Unlike macOS, LiveKit publishes Windows binaries,
# so nothing is built from source. Skipped when this version is already there.
param(
    [Parameter(Mandatory)] [string] $Version,
    [Parameter(Mandatory)] [string] $Binaries
)
$ErrorActionPreference = 'Stop'

# From the release's checksums.txt, pinned here so a changed download fails.
$sha256 = @{
    'amd64' = 'fd4b7c2c3c1e4c71adaa4f6a046ad1c0abaaaf1e09fae904b35bf231ffae11d2'
    'arm64' = '887587684dae37cd21db8a16c1bae0647a48868bfaf49f6dc4e5972de4d850f1'
}
if ($Version -ne '1.13.10') { throw "Pin the checksums for LiveKit $Version in $PSCommandPath" }

# Tauri names a sidecar by its target triple.
$triple = (rustc --print host-tuple).Trim()
$arch = switch -Wildcard ($triple) {
    'x86_64-*' { 'amd64' }
    'aarch64-*' { 'arm64' }
    default { throw "No LiveKit server build for $triple" }
}
$out = Join-Path $Binaries "livekit-server-$triple.exe"
if ((Test-Path $out) -and ((& $out --version) -eq "livekit-server version $Version")) { exit 0 }

$work = Join-Path ([IO.Path]::GetTempPath()) "livekit-server-$Version-$arch"
Remove-Item -Recurse -Force $work -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force $work, $Binaries | Out-Null
$zip = Join-Path $work 'server.zip'
$url = "https://github.com/livekit/livekit/releases/download/v$Version/livekit_${Version}_windows_$arch.zip"
Invoke-WebRequest -Uri $url -OutFile $zip -UseBasicParsing
$actual = (Get-FileHash -Algorithm SHA256 $zip).Hash.ToLower()
if ($actual -ne $sha256[$arch]) { throw "Checksum mismatch for $url`: $actual" }
Expand-Archive -Path $zip -DestinationPath $work
Copy-Item (Join-Path $work 'livekit-server.exe') $out -Force
Copy-Item (Join-Path $work 'LICENSE') (Join-Path $Binaries 'livekit-server-LICENSE.txt') -Force
Remove-Item -Recurse -Force $work
& $out --version
