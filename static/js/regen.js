// Performanter Canvas-basierter Regen-Effekt für die Zeitanzeige-Box.
// Nutzt einen einzigen requestAnimationFrame-Loop statt vieler einzelner
// CSS-Animationen, um die Seite (inkl. Zeitanzeige) flüssig zu halten.
(function () {
    const ANZAHL_TROPFEN = 140;

    function init() {
        const container = document.getElementById('rainContainer');
        if (!container) return;

        const canvas = document.createElement('canvas');
        container.appendChild(canvas);
        const ctx = canvas.getContext('2d');

        let breite = 0;
        let hoehe = 0;
        let tropfen = [];
        let dpr = Math.min(window.devicePixelRatio || 1, 2); // Performance: DPR deckeln

        function neuerTropfen(zufaelligeHoehe) {
            return {
                x: Math.random() * breite,
                y: zufaelligeHoehe ? Math.random() * hoehe : -20,
                laenge: Math.random() * 14 + 8,
                geschwindigkeit: Math.random() * 90 + 70, // px/Sekunde
                opacity: Math.random() * 0.5 + 0.25
            };
        }

        function groesseAnpassen() {
            const rect = container.getBoundingClientRect();
            breite = rect.width;
            hoehe = rect.height;
            canvas.width = breite * dpr;
            canvas.height = hoehe * dpr;
            ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        }

        function initTropfen() {
            tropfen = [];
            for (let i = 0; i < ANZAHL_TROPFEN; i++) {
                tropfen.push(neuerTropfen(true));
            }
        }

        let letzterZeitstempel = null;

        function frame(zeitstempel) {
            if (letzterZeitstempel === null) letzterZeitstempel = zeitstempel;
            const delta = Math.min((zeitstempel - letzterZeitstempel) / 1000, 0.05); // Sekunden, gedeckelt
            letzterZeitstempel = zeitstempel;

            ctx.clearRect(0, 0, breite, hoehe);
            ctx.strokeStyle = 'rgba(255, 255, 255, 1)';
            ctx.lineWidth = 2;
            ctx.lineCap = 'round';

            for (let i = 0; i < tropfen.length; i++) {
                const t = tropfen[i];
                t.y += t.geschwindigkeit * delta;

                if (t.y - t.laenge > hoehe) {
                    tropfen[i] = neuerTropfen(false);
                    continue;
                }

                ctx.globalAlpha = t.opacity;
                ctx.beginPath();
                ctx.moveTo(t.x, t.y - t.laenge);
                ctx.lineTo(t.x, t.y);
                ctx.stroke();
            }
            ctx.globalAlpha = 1;

            requestAnimationFrame(frame);
        }

        groesseAnpassen();
        initTropfen();
        requestAnimationFrame(frame);

        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(groesseAnpassen, 200);
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
