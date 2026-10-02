# 스타폭스 어드벤처 한글 패처 (게임큐브용 파일 단위 패처, 게임 정보는 data/config.txt)
# 원본 ISO를 복사한 뒤 바뀐 게임 파일만 차분 적용해 디스크 끝 빈 곳에 쓰고,
# 파일 목록(FST)의 위치·크기와 헤더의 게임 이름만 고친다. 게임큐브 디스크는 암호화가 없어서 다시 묶을 필요가 없다.
# 덤프마다 빈 영역(정크 데이터)이 달라 ISO 전체 MD5가 달라도, 게임 파일만 같으면 적용된다.
# CISO·WIA·WDF·GCZ 는 동봉한 wit 으로 ISO로 바꾼 뒤 적용한다. RVZ·NKit 는 지원하지 않는다.
# 사용: 패치하기.bat 에 이미지를 끌어다 놓거나, 이 폴더에 이미지를 두고 실행
#       powershell -File patch.ps1 [원본 이미지] [결과 ISO]
param([string]$Src, [string]$Out)

$ErrorActionPreference = 'Stop'
$env:LANG = 'en_US.UTF-8'   # 없으면 cygwin wit 이 한글 경로를 열지 못함
[Console]::OutputEncoding = [Text.Encoding]::UTF8
$here = $PSScriptRoot
$wit = Join-Path $here 'bin\wit.exe'
$xd = Join-Path $here 'bin\xdelta3.exe'
$data = Join-Path $here 'data'
$conv = Join-Path $here '_convert.iso'
$tmpA = Join-Path $here '_tmp_a'
$tmpB = Join-Path $here '_tmp_b'
$DISC_SIZE = 1459978240
$cfg = @{}
foreach ($l in Get-Content -LiteralPath (Join-Path $data 'config.txt') -Encoding UTF8) {
    if ($l -match '^(\w+)=(.*)$') { $cfg[$Matches[1]] = $Matches[2] }
}
$script:outCreated = $false

function Cleanup {
    foreach ($p in $conv, $tmpA, $tmpB) {
        if (Test-Path -LiteralPath $p) { Remove-Item -LiteralPath $p -Force }
    }
}
function Fail($msg) {
    Write-Host ''; Write-Host "[오류] $msg" -ForegroundColor Red
    if ($script:fs) { $script:fs.Close() }
    if ($script:outCreated -and (Test-Path -LiteralPath $Out)) { Remove-Item -LiteralPath $Out -Force }
    Cleanup; exit 1
}
function Md5Bytes([byte[]]$b) {
    $m = [Security.Cryptography.MD5]::Create()
    (($m.ComputeHash($b) | ForEach-Object { $_.ToString('x2') }) -join '')
}
function U32([byte[]]$b, [int]$o) { ([uint32]$b[$o] -shl 24) -bor ([uint32]$b[$o + 1] -shl 16) -bor ([uint32]$b[$o + 2] -shl 8) -bor [uint32]$b[$o + 3] }
function PutU32([byte[]]$b, [int]$o, [uint32]$v) {
    $b[$o] = [byte](($v -shr 24) -band 0xff); $b[$o + 1] = [byte](($v -shr 16) -band 0xff)
    $b[$o + 2] = [byte](($v -shr 8) -band 0xff); $b[$o + 3] = [byte]($v -band 0xff)
}
function ReadAt($fs, [long]$off, [int]$len) {
    $buf = New-Object byte[] $len
    $fs.Position = $off; $got = 0
    while ($got -lt $len) { $r = $fs.Read($buf, $got, $len - $got); if ($r -le 0) { break }; $got += $r }
    if ($got -ne $len) { Fail '이미지가 잘려 있습니다(파일 끝을 넘어 읽음).' }
    , $buf
}

Write-Host "$($cfg.title) 한글 패처 v$($cfg.version)"
Write-Host '================================'

# 1. 원본 이미지 고르기
if (-not $Src) {
    $cand = @(Get-ChildItem -LiteralPath $here -File | Where-Object { $_.Extension -match '^\.(iso|gcm|ciso|wia|wdf|gcz)$' -and $_.Name -notmatch 'Korean' })
    if ($cand.Count -eq 1) { $Src = $cand[0].FullName }
    else {
        if ($cand.Count -gt 1) { Write-Host '이 폴더에 이미지가 여러 개 있습니다.' }
        $Src = (Read-Host '원본 이미지 경로를 입력하세요(파일을 이 창에 끌어다 놓아도 됩니다)').Trim('"', ' ')
    }
}
if (-not (Test-Path -LiteralPath $Src -PathType Leaf)) { Fail "파일이 없습니다: $Src" }
$Src = (Resolve-Path -LiteralPath $Src).Path
$ext = [IO.Path]::GetExtension($Src).ToLower()
if ($ext -eq '.rvz') { Fail 'RVZ는 지원하지 않습니다. Dolphin에서 ISO로 변환한 뒤 다시 실행하세요.' }
if ($Src -match '\.nkit\.') { Fail 'NKit 이미지는 지원하지 않습니다. NKit 도구로 원래 ISO로 되돌린 뒤 다시 실행하세요.' }
if (-not $Out) { $Out = Join-Path ([IO.Path]::GetDirectoryName($Src)) "$($cfg.result).iso" }
if ($Out -eq $Src) { Fail '결과 파일이 원본과 같은 경로입니다.' }
Write-Host "원본: $Src"
Write-Host "결과: $Out"
Cleanup

# 2. ISO가 아니면 ISO로 바꾸기
$iso = $Src
if ($ext -notin '.iso', '.gcm') {
    Write-Host ''
    Write-Host '[0/3] ISO로 변환 중...'
    & $wit copy $Src $conv --iso -q -o
    if ($LASTEXITCODE -ne 0) { Fail "ISO로 변환하지 못했습니다(wit 코드 $LASTEXITCODE)." }
    $iso = $conv
}

# 3. 게임 확인
$fs0 = [IO.File]::OpenRead($iso)
$head = New-Object byte[] 0x440; [void]$fs0.Read($head, 0, 0x440); $fs0.Close()
$gid = [Text.Encoding]::ASCII.GetString($head, 0, 6)
if ($gid -ne $cfg.id) { Fail "$($cfg.title) 일본판($($cfg.id))이 아닙니다. 읽은 게임 ID: $gid" }
if ($head[7] -ne [byte]$cfg.rev) { Fail "Rev $($cfg.rev) 디스크가 아닙니다(읽은 버전: Rev $($head[7]))." }

# 4. 복사
Write-Host ''
Write-Host '[1/3] 원본 복사 중...'
if (Test-Path -LiteralPath $Out) { Remove-Item -LiteralPath $Out -Force }
if ($iso -eq $conv) { Move-Item -LiteralPath $conv -Destination $Out } else { Copy-Item -LiteralPath $iso -Destination $Out }
$script:outCreated = $true
$script:fs = [IO.File]::Open($Out, 'Open', 'ReadWrite')
$fs = $script:fs
if ($fs.Length -gt $DISC_SIZE) { $fs.SetLength($DISC_SIZE) }   # wit 변환본은 4.7GB로 커지므로 원래 크기로

# 5. 파일 목록(FST) 읽기
$fo = U32 $head 0x424; $fsz = U32 $head 0x428
$fst = ReadAt $fs $fo $fsz
$n = U32 $fst 8; $st = $n * 12
$sjis = [Text.Encoding]::GetEncoding(932)
$idx = @{}
$end = [long]0
function Name([int]$o) { $e = $st + $o; while ($fst[$e] -ne 0) { $e++ }; $sjis.GetString($fst, $st + $o, $e - $st - $o) }
function Walk([int]$i, [int]$stop, [string]$pre) {
    while ($i -lt $stop) {
        $no = ([int]$fst[$i * 12 + 1] -shl 16) -bor ([int]$fst[$i * 12 + 2] -shl 8) -bor [int]$fst[$i * 12 + 3]
        $nxt = U32 $fst ($i * 12 + 8)
        if ($fst[$i * 12] -ne 0) { Walk ($i + 1) $nxt ($pre + (Name $no) + '/'); $i = $nxt }
        else {
            $idx[$pre + (Name $no)] = $i
            $e = [long](U32 $fst ($i * 12 + 4)) + $nxt
            if ($e -gt $script:end) { $script:end = $e }
            $i++
        }
    }
}
$script:end = [long]0
Walk 1 $n ''
$pos = [long]([math]::Ceiling($script:end / 0x8000) * 0x8000)

# 6. 파일별 차분 적용 → 디스크 끝 빈 곳에 쓰고 FST 고치기
Write-Host '[2/3] 한글 패치 적용 중...'
$lines = @(Get-Content -LiteralPath (Join-Path $data 'manifest.txt') -Encoding UTF8 | Where-Object { $_ })
$k = 0
foreach ($line in $lines) {
    $mode, $patch, $rel, $srcMd5, $dstMd5 = $line -split "`t"
    $k++
    Write-Progress -Activity '한글 패치 적용' -Status $rel -PercentComplete ($k * 100 / $lines.Count)
    if (-not $idx.ContainsKey($rel)) { Fail "게임 파일이 없습니다: $rel" }
    $ei = $idx[$rel]
    $off = U32 $fst ($ei * 12 + 4); $len = U32 $fst ($ei * 12 + 8)
    $orig = ReadAt $fs $off $len
    if ((Md5Bytes $orig) -ne $srcMd5) { Fail "원본 게임 파일이 다릅니다: $rel`n  $($cfg.id) Rev $($cfg.rev) 원본인지, 이미 패치한 이미지가 아닌지 확인하세요." }
    [IO.File]::WriteAllBytes($tmpA, $orig)
    & $xd -d -f -s $tmpA (Join-Path $data $patch) $tmpB
    if ($LASTEXITCODE -ne 0) { Fail "차분 적용 실패(xdelta3 코드 $LASTEXITCODE): $rel" }
    $new = [IO.File]::ReadAllBytes($tmpB)
    if ((Md5Bytes $new) -ne $dstMd5) { Fail "패치 결과가 다릅니다: $rel" }
    if ($pos + $new.Length -gt $DISC_SIZE) { Fail '디스크 용량이 부족합니다.' }
    $fs.Position = $pos; $fs.Write($new, 0, $new.Length)
    PutU32 $fst ($ei * 12 + 4) ([uint32]$pos); PutU32 $fst ($ei * 12 + 8) ([uint32]$new.Length)
    $pos = [long]([math]::Ceiling(($pos + $new.Length) / 4) * 4)
}
Write-Progress -Activity '한글 패치 적용' -Completed
Write-Host "  파일 $($lines.Count)개 적용"

# 7. FST·게임 이름 쓰기
Write-Host '[3/3] 마무리 중...'
$fs.Position = $fo; $fs.Write($fst, 0, $fst.Length)
$name = New-Object byte[] 0x40
$nb = [Text.Encoding]::ASCII.GetBytes($cfg.discname)
[Array]::Copy($nb, $name, [math]::Min($nb.Length, 0x40))
$fs.Position = 0x20; $fs.Write($name, 0, 0x40)
$fs.Close(); $script:fs = $null
Cleanup
Write-Host ''
Write-Host "완료: $Out" -ForegroundColor Green
