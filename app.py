<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8" />
  <title>Outils Réseau</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-900 text-white p-6 font-sans">
  <div class="max-w-3xl mx-auto">
    <h1 class="text-4xl font-bold mb-6">🛠️ Outils Réseau</h1>

    <div class="space-x-2 mb-4">
      <button onclick="showTab('mac')" class="px-4 py-2 bg-indigo-600 rounded">🔍 Recherche MAC</button>
      <button onclick="showTab('speed')" class="px-4 py-2 bg-green-600 rounded">📶 Test Débit</button>
      <button onclick="showTab('tts')" class="px-4 py-2 bg-pink-600 rounded">🗣️ TTS</button>
    </div>

    <!-- MAC VENDOR -->
    <div id="mac" class="tab hidden">
      <h2 class="text-2xl mb-2">Recherche d'adresse MAC</h2>
      <input id="macAddress" type="text" placeholder="FC:FB:FB:01:FA:21"
        class="w-full text-black p-3 rounded mb-4" />
      <div class="flex justify-center">
        <button onclick="lookupMac()" class="bg-indigo-500 px-6 py-2 rounded">Rechercher</button>
      </div>
      <div id="macResult" class="mt-6 flex flex-col items-center bg-gray-800 rounded-xl p-6 shadow-lg w-full max-w-xl mx-auto">
        <a id="macLink" href="#" target="_blank" class="text-2xl font-bold mb-4 hidden hover:underline"></a>
        <img id="macLogo" src="" alt="Logo" class="h-48 w-auto hidden rounded bg-white p-1 border border-gray-300 shadow" />
        <img id="noMacFound" src="/static/sad_it.png" alt="Sad IT" class="hidden w-64 h-auto mt-6 rounded-xl shadow-xl" />
      </div>
    </div>

    <!-- SPEED TEST -->
    <div id="speed" class="tab hidden">
      <h2 class="text-2xl mb-2">Test de débit MikroTik</h2>
      <input id="targetIp" type="text" placeholder="IP publique"
        class="w-full text-black p-2 rounded mb-2" />
      <input id="targetUser" type="text" placeholder="Utilisateur"
        class="w-full text-black p-2 rounded mb-2" />
      <input id="targetPass" type="password" placeholder="Mot de passe"
        class="w-full text-black p-2 rounded mb-2" />
      <button onclick="runSpeedTest()" class="bg-green-600 px-4 py-2 rounded">Lancer</button>
      <pre id="speedResult" class="mt-4 whitespace-pre-wrap text-sm"></pre>
    </div>

    <!-- TTS -->
    <div id="tts" class="tab hidden">
      <h2 class="text-2xl mb-2">Synthèse vocale (ElevenLabs)</h2>
      <textarea id="ttsText" rows="4" class="w-full p-3 text-black rounded mb-2" placeholder="Texte à lire..."></textarea>
      <select id="ttsLang" class="w-full p-2 text-black rounded mb-2">
        <option value="EXAVITQu4vr4xnSDxMaL">🇫🇷 Jessy</option>
        <option value="jBpfuIE2acCO8z3wKNLl">🇫🇷 Gabriel</option>
        <option value="AZnzlk1XvdvUeBnXmlld">🇬🇧 Matilda</option>
      </select>
      <button onclick="runTTS()" class="bg-pink-600 px-6 py-2 rounded">Lire</button>
      <div id="ttsResult" class="mt-6 space-y-4">
        <audio id="audioPlayer" controls class="w-full hidden">
          <source id="audioSource" src="" type="audio/mp3">
        </audio>
        <a id="downloadLink" href="#" class="underline text-blue-400 hidden" download>Télécharger le fichier MP3</a>
      </div>
    </div>
  </div>

  <script>
    function showTab(id) {
      document.querySelectorAll('.tab').forEach(t => t.classList.add('hidden'));
      document.getElementById(id).classList.remove('hidden');
    }
    showTab('mac');

    async function lookupMac() {
      const mac = document.getElementById("macAddress").value.trim();
      const logo = document.getElementById("macLogo");
      const link = document.getElementById("macLink");
      const sadImg = document.getElementById("noMacFound");

      link.textContent = "Recherche...";
      link.href = "#";
      link.classList.remove("text-red-500", "hidden");
      logo.classList.add("hidden");
      sadImg.classList.add("hidden");

      try {
        const res = await fetch('/mac?address=' + encodeURIComponent(mac));
        const data = await res.json();

        if (res.ok && data.vendor && data.vendor !== "Inconnu") {
          const vendor = data.vendor;
          link.textContent = vendor;
          link.href = `https://www.google.com/search?q=${encodeURIComponent(vendor)}`;

          // Charge proprement le logo
          logo.onload = () => {
            logo.classList.remove("hidden");
          };
          logo.onerror = () => {
            logo.classList.add("hidden");
          };
          logo.src = `/logo?vendor=${encodeURIComponent(vendor)}`;
        } else {
          link.textContent = "❌ Pas de correspondance d'adresse MAC";
          link.classList.add("text-red-500");
          sadImg.classList.remove("hidden");
        }
      } catch (e) {
        link.textContent = "❌ Erreur réseau.";
        link.classList.add("text-red-500");
        sadImg.classList.remove("hidden");
      }
    }

    async function runSpeedTest() {
      const ip = document.getElementById("targetIp").value;
      const user = document.getElementById("targetUser").value;
      const pass = document.getElementById("targetPass").value;
      const result = document.getElementById("speedResult");
      result.textContent = "Test en cours...";
      try {
        const res = await fetch(`/speedtest?ip=${ip}&user=${user}&pass=${pass}`);
        result.textContent = await res.text();
      } catch (e) {
        result.textContent = "Erreur réseau.";
      }
    }

    async function runTTS() {
      const text = document.getElementById("ttsText").value.trim();
      const voice_id = document.getElementById("ttsLang").value;
      const audio = document.getElementById("audioPlayer");
      const source = document.getElementById("audioSource");
      const link = document.getElementById("downloadLink");

      if (!text) {
        alert("Veuillez entrer du texte.");
        return;
      }

      const res = await fetch("/tts", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ text, voice_id })
      });

      const data = await res.json();
      if (data.audio) {
        source.src = data.audio;
        audio.classList.remove("hidden");
        audio.load();
        audio.play();
        link.href = data.audio;
        link.classList.remove("hidden");
      } else {
        alert("Erreur : " + (data.error || "inconnue"));
      }
    }
  </script>
</body>
</html>
