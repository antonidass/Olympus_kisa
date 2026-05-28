$ErrorActionPreference = "Stop"

# Канон громкостей SFX переходов (эталон — Персей и Медуза):
#   WHOOSH.mp3        — vol 0.70  для Влево/Вправо/Вверх/Вниз/Взмах лапки
#   Swoosh (CapCut)   — vol 0.646 для Резкий зум / Зум с тряской / Переход-зум
#   Crumpled paper    — vol 1.00  для «Бумажный шар»

$draftDir = "$env:LOCALAPPDATA\CapCut\User Data\Projects\com.lveditor.draft\Каллисто и Аркас"
$src = Join-Path $draftDir "draft_content.json"

$json = Get-Content -Raw -Encoding UTF8 $src | ConvertFrom-Json

# 1) Нормализуем громкости существующих SFX-сегментов в track 14 "sfx"
$track = $json.tracks[14]
if ($track.name -ne "sfx") { throw "track 14 не sfx, прерываюсь" }

$audios = @{}
foreach ($a in $json.materials.audios) { $audios[$a.id] = $a }

$changed = @()
foreach ($seg in $track.segments) {
    $mat = $audios[$seg.material_id]
    if (-not $mat) { continue }
    $name = $mat.name
    $oldVol = $seg.volume
    $newVol = $oldVol
    if ($name -eq "Swoosh") { $newVol = 0.6456542611122131 }
    elseif ($name -eq "Swish") { $newVol = 0.7 }
    elseif ($name -eq "WHOOSH.mp3") { $newVol = 0.7 }
    elseif ($name -eq "Crumpled paper") { $newVol = 1.0 }
    if ($newVol -ne $oldVol) {
        $seg.volume = $newVol
        $changed += "$($name) @ $([math]::Round($seg.target_timerange.start/1000000,3))s : $oldVol -> $newVol"
    }
}
Write-Output "=== Изменения громкости ==="
$changed | ForEach-Object { Write-Output "  $_" }

# 2) Добавляем WHOOSH.mp3 на стык сцен 01->02 (boundary 7.583s) для перехода «Влево»
#    Старт 7.283s (за 0.3с до cut), длительность 0.6с, vol 0.7
$existingWhoosh = $null
foreach ($a in $json.materials.audios) {
    if ($a.name -eq "WHOOSH.mp3") { $existingWhoosh = $a; break }
}

function New-Guid36 { return ([guid]::NewGuid().ToString().ToUpper()) }

if (-not $existingWhoosh) {
    Write-Output "WHOOSH.mp3 material не найден — создаю"
    $whooshId = New-Guid36
    $whooshMat = [pscustomobject]@{
        id = $whooshId
        type = "extract_music"
        name = "WHOOSH.mp3"
        duration = 916666
        path = "C:\Users\Антон\Desktop\BOGI AI\assets\audio\WHOOSH.mp3"
        category_name = "local"
        wave_points = @()
        music_id = "2a838deeaabb4a76857cfd57b2714ffa"
        app_id = 0
        text_id = ""
        tone_type = ""
        source_platform = 0
        video_id = ""
        effect_id = ""
        resource_id = ""
        third_resource_id = ""
        category_id = ""
        intensifies_path = ""
        formula_id = ""
        check_flag = 3
        team_id = ""
        local_material_id = "2a838deeaabb4a76857cfd57b2714ffa"
        copyright_limit_type = "none"
    }
    $json.materials.audios += $whooshMat
} else {
    $whooshId = $existingWhoosh.id
    Write-Output "Использую существующий WHOOSH.mp3 material id=$whooshId"
}

# Создаём вспомогательные refs (speed/placeholder/sound_channel/vocal_separation)
$speedId = New-Guid36
$json.materials.speeds += [pscustomobject]@{
    id = $speedId; type = "speed"; mode = 0; speed = 1.0; curve_speed = $null
}
$placeholderId = New-Guid36
$json.materials.placeholder_infos += [pscustomobject]@{
    id = $placeholderId; type = "placeholder_info"; meta_type = "none"
    res_path = ""; res_text = ""; error_path = ""; error_text = ""
}
$scmId = New-Guid36
$json.materials.sound_channel_mappings += [pscustomobject]@{
    id = $scmId; type = "none"; audio_channel_mapping = 0; is_config_open = $false
}
$vsId = New-Guid36
$json.materials.vocal_separations += [pscustomobject]@{
    id = $vsId; type = "vocal_separation"; choice = 0; removed_sounds = @()
    time_range = $null; production_path = ""; final_algorithm = ""; enter_from = ""
}

# Новый сегмент
$segId = New-Guid36
$startUs = 7283333
$durUs = 600000
$newSeg = [pscustomobject]@{
    id = $segId
    source_timerange = [pscustomobject]@{ start = 0; duration = $durUs }
    target_timerange = [pscustomobject]@{ start = $startUs; duration = $durUs }
    render_timerange = [pscustomobject]@{ start = 0; duration = 0 }
    desc = ""
    state = 0
    speed = 1.0
    is_loop = $false
    is_tone_modify = $false
    reverse = $false
    intensifies_audio = $false
    cartoon = $false
    volume = 0.7
    last_nonzero_volume = 1.0
    clip = $null
    uniform_scale = $null
    material_id = $whooshId
    extra_material_refs = @($speedId, $placeholderId, $scmId, $vsId)
    render_index = 0
    keyframe_refs = @()
    enable_lut = $false
    enable_adjust = $false
    enable_hsl = $false
    visible = $true
    group_id = ""
    enable_color_curves = $true
    enable_hsl_curves = $true
    track_render_index = 0
    hdr_settings = $null
    enable_color_wheels = $true
    track_attribute = 0
    is_placeholder = $false
    template_id = ""
    enable_smart_color_adjust = $false
    template_scene = "default"
    common_keyframes = @()
    caption_info = $null
    responsive_layout = [pscustomobject]@{
        enable = $false; target_follow = ""; size_layout = 0
        horizontal_pos_layout = 0; vertical_pos_layout = 0
    }
    enable_color_match_adjust = $false
    enable_color_correct_adjust = $false
    enable_adjust_mask = $false
    raw_segment_id = ""
    lyric_keyframes = $null
    enable_video_mask = $true
    digital_human_template_group_id = ""
    color_correct_alg_result = ""
    source = "segmentsourcenormal"
}

# Вставляем в начало segments (трек упорядочен по времени)
$existing = $track.segments
$newList = @($newSeg) + @($existing)
$track.segments = $newList

Write-Output "=== Добавлен сегмент ==="
Write-Output "  WHOOSH.mp3 @ 7.283s dur 0.6s vol 0.7 (для перехода «Влево» на стыке 01->02)"

# Сохраняем
$jsonStr = $json | ConvertTo-Json -Depth 50 -Compress
[System.IO.File]::WriteAllText($src, $jsonStr, [System.Text.UTF8Encoding]::new($false))
Write-Output "=== Сохранено ==="
Write-Output $src
