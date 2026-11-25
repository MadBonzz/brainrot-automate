$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$source = @'
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Speech.Synthesis;
using System.Speech.AudioFormat;
public static class FilmNarrator {
    public static void Record(string text, string output, string marks) {
        var rows = new List<string>();
        using (var synth = new SpeechSynthesizer()) {
            var voice = Environment.GetEnvironmentVariable("FILM_VOICE");
            if (!String.IsNullOrWhiteSpace(voice)) synth.SelectVoice(voice);
            synth.Rate = 1;
            synth.SpeakProgress += (sender, e) => {
                rows.Add(String.Format(CultureInfo.InvariantCulture, "{0}\t{1}\t{2}", e.CharacterPosition, e.CharacterCount, e.AudioPosition.TotalSeconds));
            };
            synth.SetOutputToWaveFile(output, new SpeechAudioFormatInfo(24000, AudioBitsPerSample.Sixteen, AudioChannel.Mono));
            synth.Speak(text);
            synth.SetOutputToNull();
        }
        File.WriteAllLines(marks, rows.ToArray());
    }
}
'@
Add-Type -TypeDefinition $source -ReferencedAssemblies ([System.Speech.Synthesis.SpeechSynthesizer].Assembly.Location)
$text = [IO.File]::ReadAllText($env:FILM_LINE_FILE)
[FilmNarrator]::Record($text, $env:FILM_WAVE_FILE, $env:FILM_MARK_FILE)
