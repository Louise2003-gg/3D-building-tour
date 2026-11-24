$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Drawing
$out=Join-Path $PSScriptRoot 'models/Atrium/Studio/Textures'
[void][IO.Directory]::CreateDirectory($out)
function Brush($c){[Drawing.SolidBrush]::new([Drawing.ColorTranslator]::FromHtml($c))}
function Rect($x,$y,$w,$h,$c){$b=Brush $c;$g.FillRectangle($b,$x,$y,$w,$h);$b.Dispose()}
function Text($s,$x,$y,$size,$c){$b=Brush $c;$f=[Drawing.Font]::new('Segoe UI',$size,[Drawing.FontStyle]::Regular,[Drawing.GraphicsUnit]::Pixel);$g.DrawString($s,$f,$b,$x,$y);$f.Dispose();$b.Dispose()}
foreach($kind in @('library','studio','welcome','security','keys','blocks','cartons')){
  $bmp=[Drawing.Bitmap]::new(1536,896);$g=[Drawing.Graphics]::FromImage($bmp)
  $g.ScaleTransform(2,2)
  $g.TextRenderingHint=[Drawing.Text.TextRenderingHint]::AntiAliasGridFit
  if($kind -eq 'cartons'){
    Rect 0 0 768 448 '#FCF2DD'
    foreach($k in 0..5){
      $x=256*($k%3);$y=224*[math]::Floor($k/3)
      $tone=@('#557C74','#A46D5D','#648399','#AF8758','#777D65','#9B7986')[$k]
      Rect ($x+3) ($y+3) 250 218 '#F7ECD6';Rect ($x+3) ($y+3) 250 29 $tone
      Text 'L I T T L E   H O U S E' ($x+15) ($y+4) 17 '#FFFFFF'
      Text @('Cotton','Meadow','Moonlight','Honeycomb','Fern','Petal')[$k] ($x+12) ($y+43) 40 $tone
      Text @('soft washcloths','stacking cups','bedtime set','wooden shapes','muslin wrap','care essentials')[$k] ($x+15) ($y+100) 20 '#4D5148'
      Rect ($x+16) ($y+146) 210 2 $tone;Text 'NURSERY COLLECTION' ($x+15) ($y+158) 13 '#5D655B'
      for($j=0;$j -lt 22;$j++){Rect ($x+145+$j*3) ($y+187) (1+$j%2) 18 '#514F46'}
      Text ('0'+($k+1)) ($x+15) ($y+180) 20 $tone
    }
  }elseif($kind -eq 'blocks'){
    Rect 0 0 768 448 '#C6A06E'
    for($k=0;$k -lt 3;$k++){
      $x=256*$k
      Rect ($x+9) 16 238 416 @('#658B82','#C17F69','#C5A05C')[$k]
      Rect ($x+18) 30 220 387 '#E8CAA0'
      Rect ($x+28) 46 200 357 @('#63867E','#B87968','#BD9B59')[$k]
      Text @('A','B','C')[$k] ($x+32) 106 190 '#F9E5BF'
      Text @('01','02','03')[$k] ($x+99) 332 31 '#F9E5BF'
    }
  }elseif($kind -eq 'keys'){
    Rect 0 0 768 448 '#313538'
    $rows=@('esc|F1|F2|F3|F4|F5|F6|F7|F8|F9|F10|F11|F12','~|1|2|3|4|5|6|7|8|9|0|-|=|del','tab|Q|W|E|R|T|Y|U|I|O|P|[|]','caps|A|S|D|F|G|H|J|K|L|;|enter','shift|Z|X|C|V|B|N|M|,|.|/|shift','ctrl|alt|cmd|SPACE|alt|ctrl|<|v|>')
    for($r=0;$r -lt 6;$r++){
      $labels=$rows[$r].Split('|');$unit=740/($labels.Count+$(if($r -eq 5){5}else{0}));$x=14
      foreach($s in $labels){$width=if($s -eq 'SPACE'){6*$unit}else{$unit};$y=12+$r*71
        Rect $x $y ($width-3) 64 '#171B1C';Rect ($x+2) ($y+2) ($width-7) 57 '#565A5B';Rect ($x+3) ($y+4) ($width-9) 53 '#444849'
        if($s -ne 'SPACE'){Text $s ($x+5) ($y+4) 15 '#E7E6DC'};$x+=$width
      }
    }
  }else{
    Rect 0 0 768 448 '#F3F1EA';Rect 0 0 768 24 '#202C31';Text 'ATRIUM   /   WORKSPACE' 11 3 12 '#DBE6DB';Text '09:41     WIFI   100%' 632 3 12 '#CBD6C8'
    Rect 0 24 134 424 '#284A48';Text 'a.' 15 35 45 '#F6E4BE'
    foreach($r in 0..3){Text @('Overview','Collections','Schedule','Settings')[$r] 17 (116+$r*45) 16 '#DAE4DA'}
    $title=@{library='Library catalogue';studio='Study planner';welcome='Reception';security='Visitor desk'}[$kind]
    Text 'ATR I U M    /    TODAY' 157 48 13 '#677F72';Text $title 154 75 34 '#243F40'
    if($kind -eq 'library'){
      Rect 160 138 575 34 '#FFFFFF';Text 'Search books, topics and journals...' 173 145 15 '#83918B'
      for($k=0;$k -lt 3;$k++){$x=163+194*$k;Rect $x 198 155 125 @('#AC775F','#849A8C','#C7A470')[$k];Rect ($x+7) 203 3 114 '#F2DBBA';Text @('FORM','FIELD','COLOUR')[$k] ($x+17) 218 21 '#FFF3DA';Text @('and space','notebook','studies')[$k] ($x+17) 246 16 '#FFF3DA';Text @('Architecture','Botany','Visual design')[$k] $x 340 18 '#364C48'}
    }else{
      Text @{'studio'='Weekly timetable';'welcome'='Appointments   /   front office';'security'='Building services   /   visits'}[$kind] 160 141 18 '#536F66'
      for($k=0;$k -lt 4;$k++){$y=183+53*$k;Rect 160 $y 576 41 '#FFFFFF';Rect 161 $y 4 41 @('#BD9379','#648C80','#BEA271','#78909D')[$k];Text @('09:00','10:30','13:00','15:30')[$k] 174 ($y+10) 15 '#536961';Text @('Morning session','Study consultation','Afternoon session','Open desk')[$k] 260 ($y+8) 18 '#324A48';Text 'SCHEDULED' 631 ($y+12) 11 '#73917C'}
    }
    Rect 135 408 633 40 '#E8EBE2';Text 'Student services   /   Atrium Building' 158 419 13 '#66766E'
  }
  $bmp.Save((Join-Path $out "$kind.png"),[Drawing.Imaging.ImageFormat]::Png);$g.Dispose();$bmp.Dispose()
}
