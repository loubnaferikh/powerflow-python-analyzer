/* ================================
   FONCTIONS DE BASE PÔLE LISSE
=============================== */

// Variables globales
let lastDiagramType = { lisse: 'potier', saillant: 'blondel' };
let lastComputedData = { lisse: null, saillant: null };

// Variables pour l'animation pôle lisse (AJOUTÉES comme dans pôle saillant)
let animationIntervalLisse = null;
let animationStepLisse = 0;
let animationVectorsLisse = [];
let animationProgressLisse = 0;
let isAnimatingLisse = false;
let isAnimationPausedLisse = false;
let animationSpeedLisse = 1000; // ms entre les étapes
let stepDescriptionsLisse = [];

// Variables pour l'animation et contrôle des vecteurs
let visibleVectorsLisse = {
    potier: ['Animation', 'Courbe à vide', 'Tangente', 'Points', 'Lignes'],
    behn: ['Animation', 'V', 'I', 'RsI', 'XsI', 'E']
};

let currentVisibleLisse = {
    potier: {
        'Animation': true,
        'Courbe à vide': true,
        'Tangente': true,
        'Points': true,
        'Lignes': true
    },
    behn: {
        'Animation': true,
        'V': true,
        'I': true,
        'RsI': true,
        'XsI': true,
        'E': true
    }
};

// Page Navigation
function showPage(pageId) {
    document.querySelectorAll('.page').forEach(page => {
        page.classList.remove('active');
    });
    document.getElementById(pageId).classList.add('active');
}

function selectMachineType(type) {
    if (type === 'lisse') {
        showPage('inputPageLisse');
    } else {
        showPage('inputPageSaillant');
    }
}

// Fonction pour afficher/masquer les emails des membres
function toggleEmail(emailId) {
    const emailElement = document.getElementById(emailId);
    emailElement.classList.toggle('show');
}

// Gestion du type de machine (monophasé/triphasé) - MODIFIÉE
function setupMachineTypeListeners() {
    // Pour pôle lisse
    const machineTypeRadiosLisse = document.querySelectorAll('input[name="machine-type-lisse"]');
    machineTypeRadiosLisse.forEach(radio => {
        radio.addEventListener('change', function() {
            const couplageGroup = document.getElementById('couplage-group-lisse');
            const rsDirectMonophase = document.getElementById('rs-direct-group-lisse-monophase');
            
            if (this.value === 'triphase') {
                couplageGroup.style.display = 'block';
                rsDirectMonophase.style.display = 'none';
                
                // Afficher le choix Rs/Req
                const rsChoiceGroup = document.getElementById('rs-choice-group-lisse');
                rsChoiceGroup.style.display = 'block';
                
                // Par défaut, afficher Rs direct
                const rsDirectChoice = document.getElementById('rs-direct-group-lisse-choice');
                const reqGroupChoice = document.getElementById('req-group-lisse-choice');
                rsDirectChoice.style.display = 'block';
                reqGroupChoice.style.display = 'none';
            } else {
                couplageGroup.style.display = 'none';
                rsDirectMonophase.style.display = 'block';
                
                // Masquer le choix Rs/Req
                const rsChoiceGroup = document.getElementById('rs-choice-group-lisse');
                rsChoiceGroup.style.display = 'none';
                
                // Masquer les champs de choix
                const rsDirectChoice = document.getElementById('rs-direct-group-lisse-choice');
                const reqGroupChoice = document.getElementById('req-group-lisse-choice');
                rsDirectChoice.style.display = 'none';
                reqGroupChoice.style.display = 'none';
            }
        });
    });
    
    // Gestion du changement de couplage pour pôle lisse
    const couplageRadiosLisse = document.querySelectorAll('input[name="couplage-lisse"]');
    couplageRadiosLisse.forEach(radio => {
        radio.addEventListener('change', function() {
            // Réinitialiser les champs si on change de couplage
            const reqInput = document.getElementById('req-lisse-choice');
            const rsResultat = document.getElementById('rs-resultat-lisse-choice');
            reqInput.value = '';
            rsResultat.style.display = 'none';
        });
    });
    
    // Gestion du choix Rs/Req pour pôle lisse
    const rsChoiceRadiosLisse = document.querySelectorAll('input[name="rs-choice-lisse"]');
    rsChoiceRadiosLisse.forEach(radio => {
        radio.addEventListener('change', function() {
            const rsDirectChoice = document.getElementById('rs-direct-group-lisse-choice');
            const reqGroupChoice = document.getElementById('req-group-lisse-choice');
            const rsResultat = document.getElementById('rs-resultat-lisse-choice');
            
            if (this.value === 'direct') {
                rsDirectChoice.style.display = 'block';
                reqGroupChoice.style.display = 'none';
                rsResultat.style.display = 'none';
            } else if (this.value === 'req') {
                rsDirectChoice.style.display = 'none';
                reqGroupChoice.style.display = 'block';
                rsResultat.style.display = 'none';
            }
        });
    });
}

// NOUVELLE FONCTION: Calculer Rs à partir de Req pour pôle lisse
function calculerRsFromReqLisse() {
    const machineType = document.querySelector('input[name="machine-type-lisse"]:checked').value;
    const couplage = document.querySelector('input[name="couplage-lisse"]:checked')?.value;
    const reqInput = document.getElementById('req-lisse-choice');
    const reqValue = parseFloat(reqInput.value);
    
    const rsResultat = document.getElementById('rs-resultat-lisse-choice');
    const valeurRs = document.getElementById('valeur-rs-lisse-choice');
    const rsInputMonophase = document.getElementById('rs-lisse-monophase');
    const rsInputDirectChoice = document.getElementById('rs-lisse-direct-choice');
    
    if (isNaN(reqValue) || reqValue <= 0) {
        alert('Veuillez entrer une valeur valide pour Req (résistance totale aux bornes du stator).');
        return;
    }
    
    let rsCalculated = 0;
    let formule = '';
    
    if (machineType === 'triphase') {
        if (couplage === 'etoile') {
            // Pour couplage étoile: Req = 2*Rs => Rs = Req/2
            rsCalculated = reqValue / 2;
            formule = 'Rs = Req/2';
        } else if (couplage === 'triangle') {
            // Pour couplage triangle: Req = (2*Rs)/3 => Rs = (3*Req)/2
            rsCalculated = (3 * reqValue) / 2;
            formule = 'Rs = (3×Req)/2';
        }
    }
    
    // Afficher le résultat
    valeurRs.textContent = `${rsCalculated.toFixed(4)} Ω (${formule})`;
    rsResultat.style.display = 'block';
    
    // Mettre à jour la valeur dans le champ Rs approprié
    if (machineType === 'triphase') {
        rsInputDirectChoice.value = rsCalculated.toFixed(4);
    } else {
        rsInputMonophase.value = rsCalculated.toFixed(4);
    }
    
    // Faire défiler jusqu'au résultat
    rsResultat.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// Fonction pour obtenir la valeur de Rs pour pôle lisse (adaptée à la nouvelle interface)
function getRsValueLisse() {
    const machineType = document.querySelector('input[name="machine-type-lisse"]:checked').value;
    
    if (machineType === 'monophase') {
        const rsInput = document.getElementById('rs-lisse-monophase');
        return parseFloat(rsInput.value) || 0;
    } else {
        const rsChoice = document.querySelector('input[name="rs-choice-lisse"]:checked')?.value;
        
        if (rsChoice === 'direct') {
            const rsInput = document.getElementById('rs-lisse-direct-choice');
            return parseFloat(rsInput.value) || 0;
        } else {
            // Si l'utilisateur a choisi Req mais n'a pas calculé Rs
            // On vérifie si le calcul a été fait
            const rsResultat = document.getElementById('rs-resultat-lisse-choice');
            if (rsResultat.style.display === 'none') {
                // Si non, on demande de calculer
                alert('Veuillez d\'abord calculer Rs à partir de Req.');
                return 0;
            } else {
                const rsInput = document.getElementById('rs-lisse-direct-choice');
                return parseFloat(rsInput.value) || 0;
            }
        }
    }
}

// Table Row Management pour pôle lisse
function addRowVide(type) {
    const tableId = `table-vide-${type}`;
    const tbody = document.querySelector(`#${tableId} tbody`);
    const row = tbody.insertRow();
    row.innerHTML = `
        <td><input type="number" step="0.01" placeholder="Ex: 0.5"></td>
        <td><input type="number" step="0.01" placeholder="Ex: 220"></td>
        <td><button class="btn-remove" onclick="removeRow(this)">Supprimer</button></td>
    `;
}

function addRowCC(type) {
    const tableId = `table-cc-${type}`;
    const tbody = document.querySelector(`#${tableId} tbody`);
    const row = tbody.insertRow();
    row.innerHTML = `
        <td><input type="number" step="0.01" placeholder="Ex: 0.8"></td>
        <td><input type="number" step="0.01" placeholder="Ex: 10"></td>
        <td><button class="btn-remove" onclick="removeRow(this)">Supprimer</button></td>
    `;
}

function addRowDewatte(type) {
    const tableId = `table-dewatte-${type}`;
    const tbody = document.querySelector(`#${tableId} tbody`);
    const row = tbody.insertRow();
    row.innerHTML = `
        <td><input type="number" step="0.01" placeholder="Ex: 200"></td>
        <td><input type="number" step="0.01" placeholder="Ex: 5"></td>
        <td><input type="number" step="0.01" placeholder="Ex: 0.6"></td>
        <td><button class="btn-remove" onclick="removeRow(this)">Supprimer</button></td>
    `;
}

function removeRow(button) {
    const row = button.closest('tr');
    const tbody = row.parentElement;
    if (tbody.rows.length > 1) {
        row.remove();
    } else {
        const errorContainer = button.closest('.input-container').querySelector('.error-message');
        showError(errorContainer, 'Au moins une ligne est requise dans chaque tableau.');
    }
}

// Validation and Data Collection pour pôle lisse
function collectData(type) {
    const machineType = document.querySelector(`input[name="machine-type-${type}"]:checked`)?.value || 'monophase';
    
    // Obtenir Rs selon la nouvelle interface
    let rs = 0;
    if (type === 'lisse') {
        rs = getRsValueLisse();
    } else {
        rs = parseFloat(document.getElementById(`rs-${type}`)?.value) || 0;
    }
    
    const data = {
        type: type,
        machineType: machineType,
        couplage: machineType === 'triphase' ? (document.querySelector(`input[name="couplage-${type}"]:checked`)?.value || 'etoile') : null,
        rs: rs,
        freq: parseFloat(document.getElementById(`freq-${type}`)?.value) || 0,
        poles: parseInt(document.getElementById(`poles-${type}`)?.value) || 0,
        v: parseFloat(document.getElementById(`v-${type}`)?.value) || 0,
        i: parseFloat(document.getElementById(`i-${type}`)?.value) || 0,
        cosphi: parseFloat(document.getElementById(`cosphi-${type}`)?.value) || 0,
        nature: document.getElementById(`nature-${type}`)?.value || 'inductive',
        mode: document.getElementById(`mode-${type}`)?.value || 'generatrice',
        caracteristiqueVide: [],
        caracteristiqueCC: [],
        caracteristiqueDewatte: []
    };

    // Collect Vide data (J, E)
    const tableVide = document.querySelector(`#table-vide-${type} tbody`);
    if (tableVide) {
        for (let row of tableVide.rows) {
            const inputs = row.querySelectorAll('input');
            const j = parseFloat(inputs[0]?.value);
            const e = parseFloat(inputs[1]?.value);
            if (!isNaN(j) && !isNaN(e)) {
                data.caracteristiqueVide.push({ j, e });
            }
        }
    }

    // Collect CC data (J, Icc)
    const tableCC = document.querySelector(`#table-cc-${type} tbody`);
    if (tableCC) {
        for (let row of tableCC.rows) {
            const inputs = row.querySelectorAll('input');
            const jcc = parseFloat(inputs[0]?.value);
            const icc = parseFloat(inputs[1]?.value);
            if (!isNaN(jcc) && !isNaN(icc)) {
                data.caracteristiqueCC.push({ jcc, icc });
            }
        }
    }

    // Collect Dewatte data
    const tableDewatte = document.querySelector(`#table-dewatte-${type} tbody`);
    if (tableDewatte) {
        for (let row of tableDewatte.rows) {
            const inputs = row.querySelectorAll('input');
            const vd = parseFloat(inputs[0]?.value);
            const id = parseFloat(inputs[1]?.value);
            const jd = parseFloat(inputs[2]?.value);
            if (!isNaN(vd) && !isNaN(id) && !isNaN(jd)) {
                data.caracteristiqueDewatte.push({ vd, id, jd });
            }
        }
    }

    return data;
}

function validateData(data, diagramType) {
    const errorContainer = document.getElementById(`error-${data.type}`);
    
    // Check mandatory fields from section 1
    if (isNaN(data.rs) || isNaN(data.freq) || isNaN(data.poles) || data.poles <= 0) {
        showError(errorContainer, 'Tous les paramètres de la machine sont obligatoires (Rs, fréquence, nombre de paires de pôles > 0).');
        return false;
    }

    // Check mandatory fields from section 2
    if (isNaN(data.v) || isNaN(data.i) || isNaN(data.cosphi)) {
        showError(errorContainer, 'Tous les paramètres de fonctionnement sont obligatoires (V, I, cos φ).');
        return false;
    }

    if (data.cosphi < 0 || data.cosphi > 1) {
        showError(errorContainer, 'Le facteur de puissance (cos φ) doit être entre 0 et 1.');
        return false;
    }

    if (data.v <= 0 || data.i <= 0 || data.rs < 0 || data.freq <= 0) {
        showError(errorContainer, 'Les valeurs de tension, courant, résistance et fréquence doivent être positives.');
        return false;
    }

    // Check Vide data
    if (data.caracteristiqueVide.length < 1) {
        showError(errorContainer, 'La caractéristique à vide nécessite au moins 1 point.');
        return false;
    }

    // Check CC data
    if (data.caracteristiqueCC.length === 0) {
        showError(errorContainer, 'Les données de court-circuit sont obligatoires.');
        return false;
    }

    // Check Dewatté data for Potier
    if (diagramType === 'potier' && data.caracteristiqueDewatte.length === 0) {
        showError(errorContainer, 'Les données Dewatté sont obligatoires pour la méthode de Potier.');
        return false;
    }

    hideError(errorContainer);
    return true;
}

function showError(container, message) {
    if (container) {
        container.textContent = message;
        container.classList.add('show');
        container.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
}

function hideError(container) {
    if (container) {
        container.classList.remove('show');
    }
}

/* ================================
   FONCTIONS UTILITAIRES
=============================== */

function formatNumber(value, decimals) {
    return Number(value.toFixed(decimals));
}

// Fonction pour calculer la vitesse synchrone
function calculateSyncSpeed(freq, poles) {
    return (120 * freq) / (2 * poles); // en tr/min
}

function calculateStep(maxValue) {
    if (maxValue <= 0) return 1;
    
    const magnitude = Math.floor(Math.log10(maxValue));
    const scale = Math.pow(10, magnitude);
    
    if (maxValue / scale <= 2) return scale / 2;
    if (maxValue / scale <= 5) return scale;
    return scale * 2;
}

function drawArrow(ctx, x, y, size, angle) {
    ctx.save();
    ctx.translate(x, y);
    ctx.rotate(angle);
    
    ctx.beginPath();
    ctx.moveTo(0, 0);
    ctx.lineTo(-size, -size/2);
    ctx.lineTo(-size, size/2);
    ctx.closePath();
    ctx.fillStyle = '#000';
    ctx.fill();
    
    ctx.restore();
}

function drawVector(ctx, startX, startY, endX, endY, color, label) {
    // Ligne
    ctx.strokeStyle = color;
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(startX, startY);
    ctx.lineTo(endX, endY);
    ctx.stroke();
    
    // Flèche
    const angle = Math.atan2(endY - startY, endX - startX);
    ctx.save();
    ctx.translate(endX, endY);
    ctx.rotate(angle);
    
    ctx.beginPath();
    ctx.moveTo(0, 0);
    ctx.lineTo(-8, -4);
    ctx.lineTo(-8, 4);
    ctx.closePath();
    ctx.fillStyle = color;
    ctx.fill();
    
    ctx.restore();
    
    // Label
    const midX = (startX + endX) / 2;
    const midY = (startY + endY) / 2;
    
    // Position du label perpendiculaire au vecteur
    const offset = 15;
    const labelX = midX - offset * Math.sin(angle);
    const labelY = midY + offset * Math.cos(angle);
    
    ctx.fillStyle = color;
    ctx.font = 'bold 14px IBM Plex Sans';
    ctx.fillText(label, labelX, labelY);
}

function drawPotierPoint(ctx, x, y, color, size) {
    ctx.beginPath();
    ctx.arc(x, y, size, 0, Math.PI * 2);
    ctx.fillStyle = color;
    ctx.fill();
    ctx.strokeStyle = 'white';
    ctx.lineWidth = 1;
    ctx.stroke();
}

function setDiagramTitle(type, title) {
    const titleElement = document.getElementById(`diagram-title-${type}`);
    if (titleElement) {
        titleElement.textContent = title;
    }
}

function hasValidData(points) {
    if (!points || points.length === 0) return false;
    
    // Vérifier si au moins un point n'est pas à l'origine
    for (let point of points) {
        if (point.x !== undefined && Math.abs(point.x) > 0.01) return true;
        if (point.y !== undefined && Math.abs(point.y) > 0.01) return true;
        if (point.J !== undefined && Math.abs(point.J) > 0.01) return true;
        if (point.E !== undefined && Math.abs(point.E) > 0.01) return true;
    }
    
    return false;
}

/* ================================
   FONCTION PRINCIPALE POUR GÉNÉRER LES DIAGRAMMES (PÔLE LISSE)
=============================== */

function generateDiagram(type, diagramType) {
    console.log(`Génération du diagramme: ${type}, ${diagramType}`);
    
    lastDiagramType[type] = diagramType;
    
    const data = collectData(type);
    console.log('Données collectées:', data);
    
    if (!validateData(data, diagramType)) {
        console.log('Validation échouée');
        return;
    }

    // Show diagram display
    const diagramDisplay = document.getElementById(`diagram-display-${type}`);
    if (diagramDisplay) {
        diagramDisplay.classList.add('active');
        diagramDisplay.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    // Peupler les contrôles de vecteurs
    populateVectorControlsLisse(diagramType);

    // Call the appropriate computation function
    if (diagramType === 'potier') {
        console.log('Appel de computePotier');
        computePotier(type);
    } else if (diagramType === 'behn') {
        console.log('Appel de computeBehnEschenburg');
        computeBehnEschenburg(type);
    }
    setTimeout(() => {
    if (document.getElementById('animation-lisse').checked) {
        playAnimationLisse(); // Démarrer l'animation
    }
}, 100); 
}

function closeDiagram(type) {
    const diagramDisplay = document.getElementById(`diagram-display-${type}`);
    if (diagramDisplay) {
        diagramDisplay.classList.remove('active');
    }
    
    // Masquer la barre d'animation
    const animationBar = document.getElementById('animation-bar-lisse');
    if (animationBar) {
        animationBar.style.display = 'none';
    }
    
    // Arrêter l'animation si elle est en cours
    stopAnimationLisse();
}

// NOUVELLE FONCTION: Pour gérer les cases à cocher (comme dans pôle saillant)
function setupVectorControlsLisse() {
    const vectorsContainer = document.getElementById('vectors-lisse');
    if (!vectorsContainer) return;
    
    const checkboxes = vectorsContainer.querySelectorAll('input[type="checkbox"]');
    
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', () => {
            const vectorName = checkbox.getAttribute('data-vector');
            if (vectorName === 'Animation') {
                currentVisibleLisse[lastDiagramType.lisse][vectorName] = checkbox.checked;
                // Démarrer ou arrêter l'animation
                if (checkbox.checked && isAnimatingLisse === false) {
                    replayAnimationLisse();
                } else if (!checkbox.checked) {
                    stopAnimationLisse();
                }
            } else {
                currentVisibleLisse[lastDiagramType.lisse][vectorName] = checkbox.checked;
                
                // Redessiner le diagramme avec les nouveaux paramètres
                if (lastDiagramType.lisse === 'potier') {
                    computePotier('lisse');
                } else if (lastDiagramType.lisse === 'behn') {
                    computeBehnEschenburg('lisse');
                }
            }
        });
    });
}

// NOUVELLE FONCTION: Pour peupler les contrôles de vecteurs (comme dans pôle saillant)
function populateVectorControlsLisse(diagramType) {
    const vectorsContainer = document.getElementById('vectors-lisse');
    if (!vectorsContainer) return;
    
    vectorsContainer.innerHTML = '';
    
    let vectors = [];
    if (diagramType === 'potier') {
        vectors = ['Animation', 'Courbe à vide', 'Tangente', 'Points', 'Lignes'];
    } else if (diagramType === 'behn') {
        vectors = ['Animation', 'V', 'I', 'RsI', 'XsI', 'E'];
    }
    
    vectors.forEach((vector, index) => {
        const label = document.createElement('label');
        label.className = 'checkbox-label';
        const isChecked = currentVisibleLisse[diagramType] && currentVisibleLisse[diagramType][vector];
        label.innerHTML = `
            <input type="checkbox" ${isChecked ? 'checked' : ''} data-vector="${vector}">
            <span class="vector-label">${vector}</span>
        `;
        vectorsContainer.appendChild(label);
    });
    
    // Configurer les écouteurs
    setupVectorControlsLisse();
    
    // Initialiser la barre d'animation si l'animation est activée
    if (currentVisibleLisse[diagramType].Animation) {
        initStepDescriptionsLisse(diagramType);
        updateAnimationBarLisse();
    }
}

// NOUVELLE FONCTION: Pour mettre à jour les contrôles d'animation (comme dans pôle saillant)
function updateAnimationControlsLisse() {
    const animationCheckbox = document.querySelector('#vectors-lisse input[data-vector="Animation"]');
    if (animationCheckbox) {
        animationCheckbox.checked = currentVisibleLisse[lastDiagramType.lisse].Animation;
    }
    
    const replayButton = document.querySelector('.btn-replay');
    if (replayButton) {
        if (isAnimatingLisse) {
            replayButton.disabled = true;
            replayButton.innerHTML = '⏸️ Animation en cours';
        } else {
            replayButton.disabled = false;
            replayButton.innerHTML = '🔄 Revoir l\'animation';
        }
    }
}

// FONCTIONS D'ANIMATION (AJOUTÉES comme dans pôle saillant)
function stopAnimationLisse() {
    if (animationIntervalLisse) {
        clearInterval(animationIntervalLisse);
        animationIntervalLisse = null;
    }
    isAnimatingLisse = false;
    isAnimationPausedLisse = false;
    animationStepLisse = 0;
    animationProgressLisse = 0;
    updateAnimationControlsLisse();
    updateAnimationBarLisse();
}

function replayAnimationLisse() {
    if (!currentVisibleLisse[lastDiagramType.lisse] || !currentVisibleLisse[lastDiagramType.lisse].Animation) {
        // Activer l'animation si elle est désactivée
        currentVisibleLisse[lastDiagramType.lisse].Animation = true;
        updateAnimationControlsLisse();
    }
    
    stopAnimationLisse();
    
    // Initialiser les descriptions
    initStepDescriptionsLisse(lastDiagramType.lisse);
    
    if (lastDiagramType.lisse === 'potier' && lastComputedData.lisse && lastComputedData.lisse.type === 'potier') {
        startPotierAnimationLisse();
    } else if (lastDiagramType.lisse === 'behn' && lastComputedData.lisse && lastComputedData.lisse.type === 'behn') {
        startBehnAnimationLisse();
    }
    
    updateAnimationBarLisse();
}

// Initialiser les descriptions des étapes (AJOUTÉE comme dans pôle saillant)
function initStepDescriptionsLisse(diagramType) {
    if (diagramType === 'potier') {
        stepDescriptionsLisse = [
            {
                title: "Courbe à vide",
                details: "Tracé de la caractéristique à vide (E en fonction de J)",
                equation: "E = f(J)"
            },
            {
                title: "Droite entre les deux premiers points",
                details: "Tracé de la droite passant par les deux premiers points de la courbe à vide",
                equation: "y = m·x + b où m = (E₂ - E₁)/(J₂ - J₁)"
            },
            {
                title: "Points M et M'",
                details: "Point M (essai Dewatté) et M' (courant de court-circuit)",
                equation: "M(Jd, Vd), M'(Jccd, 0)"
            },
            {
                title: "Construction point N et ligne NM",
                details: "Point N déterminé à partir de M et M'",
                equation: "N(Jd - |OM'|, Vd)"
            },
            {
                title: "Parallèle passant par N",
                details: "Parallèle à la droite des deux premiers points passant par N",
                equation: "y = m·x + (Vd - m·(Jd - |OM'|))"
            },
            {
                title: "Point d'intersection T",
                details: "Intersection de la parallèle avec la courbe à vide",
                equation: "Intersection: f(J) = m·J + (Vd - m·(Jd - |OM'|))"
            },
            {
                title: "Point S et segments TS, MS",
                details: "Projection de T sur NM pour déterminer α et λ",
                equation: "α = MS/Id, λ = TS/Id"
            }
        ];
    } else if (diagramType === 'behn') {
        const results = lastComputedData.lisse?.results;
        const phiAngle = results?.phiAdjusted ? (results.phiAdjusted * 180 / Math.PI).toFixed(1) : 0;
        
        stepDescriptionsLisse = [
            {
                title: "Tension V",
                details: "Représentation du vecteur tension phase-neutre",
                equation: "V = V∠0°"
            },
            {
                title: "Courant I",
                details: "Représentation du vecteur courant avec l'angle φ",
                equation: `I = I∠${phiAngle}°`
            },
            {
                title: "Chute ohmique Rs·I",
                details: "Chute de tension due à la résistance statorique",
                equation: "Rs·I = Rs × I (en phase avec I)"
            },
            {
                title: "Chute réactive Xs·I",
                details: "Chute de tension due à la réactance synchrone",
                equation: "jXs·I = Xs × I (en quadrature avec I)"
            },
            {
                title: "Force électromotrice E",
                details: "Somme vectorielle pour obtenir la FEM interne",
                equation: results?.mode === "generatrice" 
                    ? "E = V + Rs·I + jXs·I" 
                    : "E = V + Rs·I - jXs·I"
            }
        ];
    }
}

// Mettre à jour la barre d'animation (AJOUTÉE comme dans pôle saillant)
function updateAnimationBarLisse() {
    const animationBar = document.getElementById('animation-bar-lisse');
    if (!animationBar) return;
    
    if (isAnimatingLisse || animationStepLisse > 0) {
        // Afficher la barre d'animation
        animationBar.style.display = 'block';
        
        // Mettre à jour la progression
        const progress = (animationStepLisse / animationVectorsLisse.length) * 100;
        document.getElementById('progress-fill-lisse').style.width = `${progress}%`;
        
        // Mettre à jour les labels
        document.getElementById('current-step-lisse').textContent = 
            `Étape ${animationStepLisse}`;
        document.getElementById('total-steps-lisse').textContent = 
            `sur ${animationVectorsLisse.length} étapes`;
        
        // Mettre à jour l'indicateur d'étape
        document.getElementById('step-number-lisse').textContent = 
            animationStepLisse;
        document.getElementById('step-total-lisse').textContent = 
            `sur ${animationVectorsLisse.length}`;
        
        // Mettre à jour la description
        if (animationStepLisse > 0 && animationStepLisse <= stepDescriptionsLisse.length) {
            const stepDesc = stepDescriptionsLisse[animationStepLisse - 1];
            document.getElementById('step-title-lisse').textContent = 
                `Étape ${animationStepLisse}: ${stepDesc.title}`;
            document.getElementById('step-details-lisse').textContent = stepDesc.details;
            document.getElementById('step-equation-lisse').textContent = stepDesc.equation;
            document.getElementById('step-equation-lisse').style.display = 'block';
        } else if (animationStepLisse === 0) {
            document.getElementById('step-title-lisse').textContent = 'Prêt à démarrer';
            document.getElementById('step-details-lisse').textContent = 
                'Activez l\'animation pour voir la construction étape par étape du diagramme.';
            document.getElementById('step-equation-lisse').style.display = 'none';
        }
        
        // Mettre à jour les boutons de contrôle
        const playBtn = document.getElementById('play-btn-lisse');
        const pauseBtn = document.getElementById('pause-btn-lisse');
        const restartBtn = document.getElementById('restart-btn-lisse');
        const completeDiv = document.getElementById('animation-complete-lisse');
        
        if (isAnimationPausedLisse) {
            playBtn.disabled = false;
            pauseBtn.disabled = true;
            playBtn.innerHTML = '<i class="fas fa-play"></i> Reprendre';
        } else if (isAnimatingLisse) {
            playBtn.disabled = true;
            pauseBtn.disabled = false;
            playBtn.innerHTML = '<i class="fas fa-play"></i> En cours...';
        } else {
            playBtn.disabled = false;
            pauseBtn.disabled = true;
            playBtn.innerHTML = '<i class="fas fa-play"></i> Démarrer';
        }
        
        // Afficher/masquer le message de complétion
        if (animationStepLisse >= animationVectorsLisse.length && !isAnimatingLisse) {
            completeDiv.style.display = 'block';
        } else {
            completeDiv.style.display = 'none';
        }
    } else {
        animationBar.style.display = 'none';
    }
}

// Contrôles d'animation (AJOUTÉS comme dans pôle saillant)
function playAnimationLisse() {
    if (isAnimatingLisse && !isAnimationPausedLisse) return;
    
    if (isAnimationPausedLisse) {
        // Reprendre l'animation
        isAnimationPausedLisse = false;
        updateAnimationBarLisse();
    } else if (!isAnimatingLisse) {
        // Démarrer une nouvelle animation
        replayAnimationLisse();
    }
}

function pauseAnimationLisse() {
    if (isAnimatingLisse && !isAnimationPausedLisse) {
        isAnimationPausedLisse = true;
        updateAnimationBarLisse();
    }
}

function restartAnimationLisse() {
    stopAnimationLisse();
    animationStepLisse = 0;
    updateAnimationBarLisse();
    setTimeout(() => {
        playAnimationLisse();
    }, 500);
}

// Démarrer l'animation Potier (AJOUTÉE comme dans pôle saillant)
function startPotierAnimationLisse() {
    if (!lastComputedData.lisse || lastComputedData.lisse.type !== 'potier') return;
    
    animationVectorsLisse = [];
    animationStepLisse = 0;
    animationProgressLisse = 0;
    isAnimatingLisse = true;
    isAnimationPausedLisse = false;
    
    const data = lastComputedData.lisse.results;
    
    // Initialiser la barre d'animation
    updateAnimationBarLisse();
    
    // Démarrer l'animation
    animationIntervalLisse = setInterval(animatePotierStepLisse, animationSpeedLisse);
}

// Animer une étape Potier (AJOUTÉE comme dans pôle saillant)
function animatePotierStepLisse() {
    if (isAnimationPausedLisse) return;
    
    if (animationStepLisse >= 7) { // 7 étapes pour Potier
        stopAnimationLisse();
        computePotier('lisse');
        updateAnimationBarLisse();
        return;
    }
    
    // Calculer le progrès
    animationProgressLisse = (animationStepLisse + 1) / 7;
    
    // Dessiner le diagramme avec l'animation actuelle
    drawPotierDiagramCorrect('lisse', lastComputedData.lisse.results, animationStepLisse);
    
    // Mettre à jour la barre d'animation
    updateAnimationBarLisse();
    
    animationStepLisse++;
}

// Démarrer l'animation Behn (AJOUTÉE comme dans pôle saillant)
function startBehnAnimationLisse() {
    if (!lastComputedData.lisse || lastComputedData.lisse.type !== 'behn') return;
    
    animationVectorsLisse = [];
    animationStepLisse = 0;
    animationProgressLisse = 0;
    isAnimatingLisse = true;
    isAnimationPausedLisse = false;
    
    const data = lastComputedData.lisse.results;
    
    // Initialiser la barre d'animation
    updateAnimationBarLisse();
    
    animationIntervalLisse = setInterval(animateBehnStepLisse, animationSpeedLisse);
}

// Animer une étape Behn (AJOUTÉE comme dans pôle saillant)
function animateBehnStepLisse() {
    if (isAnimationPausedLisse) return;
    
    if (animationStepLisse >= 5) { // 5 étapes pour Behn
        stopAnimationLisse();
        computeBehnEschenburg('lisse');
        updateAnimationBarLisse();
        return;
    }
    
    animationProgressLisse = (animationStepLisse + 1) / 5;
    
    // Dessiner le diagramme avec l'animation actuelle
    drawBehnDiagram('lisse', lastComputedData.lisse.results, animationStepLisse);
    
    // Mettre à jour la barre d'animation
    updateAnimationBarLisse();
    
    animationStepLisse++;
}

/* ================================
   MÉTHODE POTIER CORRIGÉE AVEC NOUVEAU CALCUL DE J (PÔLE LISSE)
=============================== */

function computePotier(type) {
    console.log('Début de computePotier pour', type);
    
    const data = collectData(type);
    
    // Validation spécifique à Potier
    const errorContainer = document.getElementById(`error-${type}`);
    if (data.caracteristiqueVide.length < 4) {
        showError(errorContainer, "La méthode de Potier nécessite au moins 4 points pour la caractéristique à vide");
        return;
    }
    
    if (data.caracteristiqueCC.length < 1) {
        showError(errorContainer, "Au moins 1 point de court-circuit est requis");
        return;
    }
    
    if (data.caracteristiqueDewatte.length === 0) {
        showError(errorContainer, "Les données Dewatté sont requises pour la méthode de Potier");
        return;
    }
    
    hideError(errorContainer);
    
    // Récupération des données
    const Rs = data.rs;
    const V = data.v; // Tension simple d'alimentation
    const I = data.i; // Courant d'induit
    const cosphi = data.cosphi;
    const nature = data.nature;
    
    // Données des essais
    const vacuumData = data.caracteristiqueVide.map(p => ({ J: p.j, E: p.e }));
    const ccData = data.caracteristiqueCC.map(p => ({ J: p.jcc, Icc: p.icc }));
    const dewatteData = data.caracteristiqueDewatte;
    
    // Utiliser le premier point dewatté
    const dewattagePoint = dewatteData[0];
    const Vd = dewattagePoint.vd;
    const Id = dewattagePoint.id;
    const Jd = dewattagePoint.jd;
    
    // 1. Calcul de la pente entre les deux premiers points de la caractéristique à vide
    const slope = calculateVacuumSlopeFirstTwoPoints(vacuumData);
    
    // 2. Calcul de Jccd à partir de l'essai en court-circuit
    const k = calculateCCSlope(ccData);
    const Jccd = Id / k;
    
    // 3. Points M et M'
    const M = { J: Jd, E: Vd };
    const Mprime = { J: Jccd, E: 0 };
    
    // 4. Construction du point N
    const distance_OMprime = Math.sqrt(Mprime.J * Mprime.J + Mprime.E * Mprime.E);
    
    const N = {
        J: M.J - distance_OMprime,
        E: M.E
    };
    
    // 5. Équation de la droite parallèle passant par N (même pente que la droite entre les deux premiers points)
    const intercept = N.E - slope * N.J;
    
    // 6. Intersection T avec la caractéristique à vide
    const T = findIntersectionPotier(vacuumData, slope, intercept);
    
    // 7. Point S (projection verticale de T sur NM)
    const S = {
        J: T.J,
        E: M.E
    };
    
    // 8. Calcul des paramètres de Potier
    const MS = Math.abs(M.J - S.J);
    const TS = Math.abs(T.E - S.E);
    
    const alpha = MS / Id;
    const lambda = TS / Id;
    
    // 9. NOUVEAU CALCUL DE J selon la méthode demandée
    // 1. alpha et lambda sont déjà calculés ci-dessus
    // 2. Calcul de Er
    let phi = Math.acos(cosphi);
    
    // Ajustement du signe de phi selon la nature de la charge
    if (nature === 'inductive') {
        // Pour charge inductive, sin(phi) > 0
        phi = Math.abs(phi);
    } else if (nature === 'capacitive') {
        // Pour charge capacitive, sin(phi) < 0
        phi = -Math.abs(phi);
    } else { // resistive
        phi = 0;
    }
    
    // Calcul de Er selon la formule: Er = √((V*cos(φ)+Rs*I)² + (V*sin(φ)+λ*I)²)
    const Er = Math.sqrt(
        Math.pow(V * Math.cos(phi) + Rs * I, 2) +
        Math.pow(V * Math.sin(phi) + lambda * I, 2)
    );
    
    // 3. Détermination de Jr à partir de la caractéristique à vide
    const Jr = interpolateJFromEPotier(vacuumData, Er);
    
    // 4. Calcul de J final: J = Jr + α*I
    const J_excitation = Jr + alpha * I;
    
    // Stocker les données pour l'affichage ultérieur
    lastComputedData[type] = {
        type: 'potier',
        results: {
            alpha: alpha,
            lambda: lambda,
            J_excitation: J_excitation,
            slope: slope,
            k: k,
            T: T,
            S: S,
            M: M,
            Mprime: Mprime,
            N: N,
            V: V,
            I: I,
            Id: Id,
            Er: Er,
            Jr: Jr,
            phi: phi,
            phiDeg: phi * 180 / Math.PI,
            Rs: Rs,
            vacuumData: vacuumData,
            nature: nature,
            firstTwoPoints: getFirstTwoPoints(vacuumData) // Stocker les deux premiers points
        }
    };
    
    // Affichage des résultats (sans J)
    displayPotierResults(type, {
        alpha: alpha,
        lambda: lambda,
        slope: slope,
        k: k,
        T: T,
        S: S,
        M: M,
        Mprime: Mprime,
        N: N,
        V: V,
        I: I,
        Id: Id,
        Er: Er,
        Jr: Jr,
        phi: phi * 180 / Math.PI
    });
    
    // Dessin du diagramme
    drawPotierDiagramCorrect(type, {
        vacuumData: vacuumData,
        ccData: ccData,
        slope: slope,
        M: M,
        Mprime: Mprime,
        N: N,
        T: T,
        S: S,
        alpha: alpha,
        lambda: lambda,
        Id: Id
    });
}

// Fonction pour obtenir les deux premiers points de la caractéristique à vide
function getFirstTwoPoints(vacuumData) {
    if (vacuumData.length < 2) return null;
    
    // Trier par J croissant
    const sortedData = [...vacuumData].sort((a, b) => a.J - b.J);
    
    return {
        point1: sortedData[0],
        point2: sortedData[1]
    };
}

// MODIFIÉ: Calcul de la pente entre les deux premiers points de la caractéristique à vide
function calculateVacuumSlopeFirstTwoPoints(vacuumData) {
    if (vacuumData.length < 2) return 0;
    
    // Obtenir les deux premiers points (triés par J croissant)
    const sortedData = [...vacuumData].sort((a, b) => a.J - b.J);
    const point1 = sortedData[0];
    const point2 = sortedData[1];
    
    // Calculer la pente K = (E2 - E1) / (J2 - J1)
    const deltaE = point2.E - point1.E;
    const deltaJ = point2.J - point1.J;
    
    // Éviter la division par zéro
    if (Math.abs(deltaJ) < 0.001) {
        // Si J1 et J2 sont trop proches, prendre le point suivant
        if (sortedData.length > 2) {
            const point3 = sortedData[2];
            return (point3.E - point1.E) / (point3.J - point1.J);
        }
        return 1; // Valeur par défaut
    }
    
    return deltaE / deltaJ;
}

// Fonction pour calculer la pente de la caractéristique CC
function calculateCCSlope(ccData) {
    if (!ccData || ccData.length === 0) return 1;
    
    if (ccData.length === 1) {
        const point = ccData[0];
        // Éviter la division par zéro
        if (Math.abs(point.J) < 0.001) {
            return (point.Icc > 0) ? point.Icc / 0.1 : 1;
        }
        return point.Icc / point.J;
    }
    
    // Trier par J croissant
    const sortedData = [...ccData].sort((a, b) => a.J - b.J);
    
    // Prendre les 2 premiers points
    const point1 = sortedData[0];
    const point2 = sortedData[1];
    
    // Vérifier la différence pour éviter la division par zéro
    if (Math.abs(point2.J - point1.J) < 0.001) {
        if (sortedData.length > 2) {
            const point3 = sortedData[2];
            return (point3.Icc - point1.Icc) / (point3.J - point1.J);
        }
        // Valeur par défaut
        return point1.Icc / Math.max(point1.J, 0.1);
    }
    
    return (point2.Icc - point1.Icc) / (point2.J - point1.J);
}

function findIntersectionPotier(data, slope, intercept) {
    const Jmin = Math.min(...data.map(d => d.J));
    const Jmax = Math.max(...data.map(d => d.J));
    
    let bestJ = Jmin;
    let minDiff = Infinity;
    
    // Recherche par dichotomie pour plus de précision
    for (let J = Jmin; J <= Jmax; J += 0.01) {
        const Ecurve = interpolateEPotier(data, J);
        const Eline = slope * J + intercept;
        const diff = Math.abs(Ecurve - Eline);
        
        if (diff < minDiff) {
            minDiff = diff;
            bestJ = J;
        }
    }
    
    const E = interpolateEPotier(data, bestJ);
    return { J: bestJ, E: E };
}

function interpolateEPotier(data, J) {
    if (data.length < 2) return 0;
    
    const sortedData = data.sort((a, b) => a.J - b.J);
    
    for (let i = 0; i < sortedData.length - 1; i++) {
        if (J >= sortedData[i].J && J <= sortedData[i+1].J) {
            const t = (J - sortedData[i].J) / (sortedData[i+1].J - sortedData[i].J);
            return sortedData[i].E + t * (sortedData[i+1].E - sortedData[i].E);
        }
    }
    
    // Extrapolation
    if (J < sortedData[0].J) {
        const m = (sortedData[1].E - sortedData[0].E) / (sortedData[1].J - sortedData[0].J);
        return sortedData[0].E + m * (J - sortedData[0].J);
    } else {
        const last = sortedData.length - 1;
        const m = (sortedData[last].E - sortedData[last-1].E) / 
                  (sortedData[last].J - sortedData[last-1].J);
        return sortedData[last].E + m * (J - sortedData[last].J);
    }
}

function interpolateJFromEPotier(data, E) {
    if (data.length < 2) return 0;
    
    const sortedData = data.sort((a, b) => a.E - b.E);
    
    for (let i = 0; i < sortedData.length - 1; i++) {
        if (E >= sortedData[i].E && E <= sortedData[i+1].E) {
            const t = (E - sortedData[i].E) / (sortedData[i+1].E - sortedData[i].E);
            return sortedData[i].J + t * (sortedData[i+1].J - sortedData[i].J);
        }
    }
    
    // Extrapolation
    if (E < sortedData[0].E) {
        const m = (sortedData[1].J - sortedData[0].J) / (sortedData[1].E - sortedData[0].E);
        return sortedData[0].J + m * (E - sortedData[0].E);
    } else {
        const last = sortedData.length - 1;
        const m = (sortedData[last].J - sortedData[last-1].J) / 
                  (sortedData[last].E - sortedData[last-1].E);
        return sortedData[last].J + m * (E - sortedData[last].E);
    }
}

function displayPotierResults(type, results) {
    const outputsContainer = document.getElementById(`outputs-${type}`);
    
    if (!outputsContainer) {
        console.error(`Container outputs-${type} non trouvé`);
        return;
    }
    
    outputsContainer.innerHTML = `
        <div class="output-item">
            <div class="output-label">Coefficient d'équivalence α</div>
            <div class="output-value">${formatNumber(results.alpha, 4)}</div>
        </div>
        <div class="output-item">
            <div class="output-label">Réactance de Potier λ</div>
            <div class="output-value">${formatNumber(results.lambda, 3)} Ω</div>
        </div>
        <div class="output-item">
            <div class="output-label">Force électromotrice Er</div>
            <div class="output-value">${formatNumber(results.Er, 2)} V</div>
        </div>
        <div class="output-item">
            <div class="output-label">Courant d'excitation Jr</div>
            <div class="output-value">${formatNumber(results.Jr, 2)} A</div>
        </div>
       
        <div class="output-item">
            <div class="output-label">Angle φ</div>
            <div class="output-value">${formatNumber(results.phi, 2)}°</div>
        </div>
        
    `;
}

function drawPotierDiagramCorrect(type, data, currentAnimationStep = -1) {
    const canvas = document.getElementById(`diagramCanvas-${type}`);
    if (!canvas) {
        console.error(`Canvas non trouvé pour ${type}`);
        return;
    }
    
    const ctx = canvas.getContext('2d');
    
    // Taille du canvas
    canvas.width = canvas.parentElement.clientWidth - 4;
    canvas.height = canvas.parentElement.clientHeight - 4;
    
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Vérifier si on a des données valides
    const allPoints = [
        ...data.vacuumData.map(p => ({ J: p.J, E: p.E })),
        data.M, data.Mprime, data.N, data.T, data.S
    ];
    
    if (!hasValidData(allPoints)) {
        ctx.fillStyle = '#666';
        ctx.font = '20px IBM Plex Sans';
        ctx.textAlign = 'center';
        ctx.fillText('Pas de données valides à afficher', canvas.width/2, canvas.height/2);
        setDiagramTitle(type, 'Diagramme de Potier - Données manquantes');
        return;
    }
    
    // Définir le titre du diagramme
    setDiagramTitle(type, 'Diagramme de Potier');
    
    // Collecte de TOUTES les données pour l'échelle
    const allPointsWithOrigin = [
        ...allPoints,
        { J: 0, E: 0 }
    ];
    
    // Calculer les limites maximales
    const maxJ = Math.max(...allPointsWithOrigin.map(p => p.J || 0), 10) * 1.1;
    const maxE = Math.max(...allPointsWithOrigin.map(p => p.E || 0), 200) * 1.1;
    
    // Marges
    const margin = 60;
    const graphWidth = canvas.width - 2 * margin;
    const graphHeight = canvas.height - 2 * margin;
    
    const scaleX = 300;
    const scaleY = graphHeight / maxE;
    
    // Fonction de conversion
    const toCanvas = (J, E) => ({
        x: margin + J * scaleX,
        y: canvas.height - margin - E * scaleY
    });
    
    // Dessiner la grille
    drawPotierGrid(ctx, canvas, margin, graphWidth, graphHeight, maxJ, maxE);
    
    // Dessiner les axes
    drawPotierAxes(ctx, canvas, margin, graphWidth, graphHeight, maxJ, maxE);
    
    // Récupérer les éléments visibles
    const visibleElements = currentVisibleLisse.potier;
    
    // Récupérer les données pour l'affichage
    const computedData = lastComputedData[type];
    const firstTwoPoints = computedData?.results?.firstTwoPoints;
    
    // Trier les points par J croissant
    const sortedVacuumData = [...data.vacuumData].sort((a, b) => a.J - b.J);
    
    if (currentAnimationStep >= 0 && isAnimatingLisse) {
        // Mode animation - dessiner étape par étape
        for (let i = 1; i <= currentAnimationStep; i++) {
            switch(i) {
                case 1:
                    // Courbe à vide
                    if (visibleElements['Courbe à vide']) {
                        drawPotierStep1(ctx, sortedVacuumData, toCanvas);
                    }
                    break;
                case 2:
                    // Droite entre les deux premiers points
                    if (visibleElements['Tangente'] && firstTwoPoints) {
                        drawPotierStep2(ctx, data, toCanvas, maxJ, firstTwoPoints);
                    }
                    break;
                case 3:
                    // Points M et M'
                    if (visibleElements['Points']) {
                        drawPotierStep3(ctx, data, toCanvas);
                    }
                    break;
                case 4:
                    // Point N et ligne NM
                    if (visibleElements['Lignes']) {
                        drawPotierStep4(ctx, data, toCanvas);
                    }
                    break;
                case 5:
                    // Parallèle passant par N
                    if (visibleElements['Tangente']) {
                        drawPotierStep5(ctx, data, toCanvas, maxJ, firstTwoPoints);
                    }
                    break;
                case 6:
                    // Point T
                    if (visibleElements['Points']) {
                        drawPotierStep6(ctx, data, toCanvas);
                    }
                    break;
                case 7:
                    // Point S et segments TS, MS
                    if (visibleElements['Lignes']) {
                        drawPotierStep7(ctx, data, toCanvas);
                    }
                    break;
            }
        }
    } else {
        // Mode normal - dessiner tous les éléments visibles
        if (visibleElements['Courbe à vide']) {
            // 1. Courbe caractéristique à vide
            ctx.beginPath();
            
            // Tracer la courbe complète
            for (let i = 0; i < sortedVacuumData.length; i++) {
                const point = toCanvas(sortedVacuumData[i].J, sortedVacuumData[i].E);
                
                if (i === 0) {
                    ctx.moveTo(point.x, point.y);
                } else {
                    const prevPoint = toCanvas(sortedVacuumData[i-1].J, sortedVacuumData[i-1].E);
                    
                    // Courbe de Bézier pour lissage
                    const cp1x = prevPoint.x + (point.x - prevPoint.x) * 0.3;
                    const cp1y = prevPoint.y + (point.y - prevPoint.y) * 0.3;
                    const cp2x = prevPoint.x + (point.x - prevPoint.x) * 0.7;
                    const cp2y = prevPoint.y + (point.y - prevPoint.y) * 0.7;
                    
                    ctx.bezierCurveTo(cp1x, cp1y, cp2x, cp2y, point.x, point.y);
                }
            }
            
            ctx.strokeStyle = '#0066cc';
            ctx.lineWidth = 3;
            ctx.stroke();
            
            // Dessin des points
            sortedVacuumData.forEach(point => {
                const p = toCanvas(point.J, point.E);
                drawPotierPoint(ctx, p.x, p.y, '#0066cc', 4);
            });
        }
        
        // 2. MODIFIÉ: Tangente entre les deux premiers points - DROITE COMPLÈTE
        if (visibleElements['Tangente'] && firstTwoPoints) {
            const point1 = firstTwoPoints.point1;
            const point2 = firstTwoPoints.point2;
            
            // Calculer la pente de la droite
            const slope = (point2.E - point1.E) / (point2.J - point1.J);
            
            // Calculer l'ordonnée à l'origine (E = slope*J + b => b = E - slope*J)
            const intercept = point1.E - slope * point1.J;
            
            // Déterminer les limites du graphique en coordonnées réelles
            // maxJ est déjà défini plus haut dans la fonction
            const maxE = Math.max(...allPointsWithOrigin.map(p => p.E || 0), 200) * 1.1;
            
            // Trouver les points d'intersection avec les bords du graphique
            // L'équation de la droite: E = slope * J + intercept
            
            // 1. Intersection avec la ligne E = 0 (axe des J)
            let startJ, startE, endJ, endE;
            
            if (Math.abs(slope) > 0.001) {
                // Quand E = 0, J = -intercept/slope
                const J_at_E0 = -intercept / slope;
                
                // Quand J = 0, E = intercept
                const E_at_J0 = intercept;
                
                // Quand J = maxJ, E = slope * maxJ + intercept
                const E_at_maxJ = slope * maxJ + intercept;
                
                // Quand E = maxE, J = (maxE - intercept)/slope
                const J_at_maxE = (maxE - intercept) / slope;
                
                // Nous voulons les intersections avec les limites du graphique visible
                // Tester quelles intersections sont dans les limites
                const candidatePoints = [];
                
                // Intersection avec l'axe J (E = 0)
                if (J_at_E0 >= 0 && J_at_E0 <= maxJ) {
                    candidatePoints.push({ J: J_at_E0, E: 0 });
                }
                
                // Intersection avec l'axe E (J = 0)
                if (E_at_J0 >= 0 && E_at_J0 <= maxE) {
                    candidatePoints.push({ J: 0, E: E_at_J0 });
                }
                
                // Intersection avec la droite J = maxJ
                if (E_at_maxJ >= 0 && E_at_maxJ <= maxE) {
                    candidatePoints.push({ J: maxJ, E: E_at_maxJ });
                }
                
                // Intersection avec la droite E = maxE
                if (J_at_maxE >= 0 && J_at_maxE <= maxJ) {
                    candidatePoints.push({ J: J_at_maxE, E: maxE });
                }
                
                // Prendre les deux points les plus éloignés
                if (candidatePoints.length >= 2) {
                    // Trier par J croissant
                    candidatePoints.sort((a, b) => a.J - b.J);
                    startJ = candidatePoints[0].J;
                    startE = candidatePoints[0].E;
                    endJ = candidatePoints[candidatePoints.length - 1].J;
                    endE = candidatePoints[candidatePoints.length - 1].E;
                } else {
                    // Si on n'a pas assez d'intersections, on étend simplement la ligne
                    startJ = Math.max(0, Math.min(point1.J, point2.J) - 0.5);
                    endJ = Math.min(maxJ, Math.max(point1.J, point2.J) + 0.5);
                    startE = slope * startJ + intercept;
                    endE = slope * endJ + intercept;
                }
            } else {
                // Pente presque nulle (droite horizontale)
                startJ = 0;
                endJ = maxJ;
                startE = intercept;
                endE = intercept;
            }
            
            // Assurer que les points sont dans les limites du graphique
            startJ = Math.max(0, Math.min(startJ, maxJ));
            endJ = Math.max(0, Math.min(endJ, maxJ));
            startE = Math.max(0, Math.min(startE, maxE));
            endE = Math.max(0, Math.min(endE, maxE));
            
            // Tracer la droite étendue jusqu'aux bords
            const pStart = toCanvas(startJ, startE);
            const pEnd = toCanvas(endJ, endE);
            
            ctx.beginPath();
            ctx.moveTo(pStart.x, pStart.y);
            ctx.lineTo(pEnd.x, pEnd.y);
            ctx.strokeStyle = '#ff9900';
            ctx.lineWidth = 2;
            ctx.setLineDash([5, 5]);
            ctx.stroke();
            ctx.setLineDash([]);
            
            // Tracer un segment plus épais pour la partie entre les deux points originaux
            const p1 = toCanvas(point1.J, point1.E);
            const p2 = toCanvas(point2.J, point2.E);
            
            ctx.beginPath();
            ctx.moveTo(p1.x, p1.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.strokeStyle = '#ff9900';
            ctx.lineWidth = 4; // Plus épais pour la partie originale
            ctx.stroke();
            
            // Calculer et afficher la pente
            ctx.fillStyle = '#ff9900';
            ctx.font = 'bold 14px IBM Plex Sans';
            ctx.fillText(`Pente: ${formatNumber(slope, 2)} V/A`, pEnd.x - 100, pEnd.y - 15);
            
            // Marquer spécialement les deux premiers points
            drawPotierPoint(ctx, p1.x, p1.y, '#ff9900', 8);
            drawPotierPoint(ctx, p2.x, p2.y, '#ff9900', 8);
            
            ctx.fillStyle = '#ff9900';
            ctx.font = 'bold 12px IBM Plex Sans';
            ctx.fillText(`(${point1.J.toFixed(2)}, ${point1.E.toFixed(1)})`, p1.x - 40, p1.y - 15);
            ctx.fillText(`(${point2.J.toFixed(2)}, ${point2.E.toFixed(1)})`, p2.x - 40, p2.y - 15);
        }
        
        // 3. Points M, M', N, T, S
        if (visibleElements['Points']) {
            const points = [
                { point: data.M, color: '#00cc66', label: 'M', offsetX: 10, offsetY: -10 },
                { point: data.Mprime, color: '#cc66ff', label: "M'", offsetX: 10, offsetY: 10 },
                { point: data.N, color: '#ff6666', label: 'N', offsetX: -15, offsetY: -10 },
                { point: data.T, color: '#cc0000', label: 'T', offsetX: 10, offsetY: -10 },
                { point: data.S, color: '#ff6600', label: 'S', offsetX: 10, offsetY: 10 }
            ];
            
            points.forEach(p => {
                const canvasPoint = toCanvas(p.point.J, p.point.E);
                drawPotierPoint(ctx, canvasPoint.x, canvasPoint.y, p.color, 6);
                
                ctx.fillStyle = p.color;
                ctx.font = 'bold 14px IBM Plex Sans';
                ctx.fillText(p.label, canvasPoint.x + p.offsetX, canvasPoint.y + p.offsetY);
            });
        }
        
        // 4. Lignes de construction
        if (visibleElements['Lignes']) {
            // Ligne OM'
            const origin = toCanvas(0, 0);
            const pMprime = toCanvas(data.Mprime.J, data.Mprime.E);
            ctx.beginPath();
            ctx.moveTo(origin.x, origin.y);
            ctx.lineTo(pMprime.x, pMprime.y);
            ctx.strokeStyle = '#cc66ff';
            ctx.lineWidth = 1;
            ctx.setLineDash([3, 3]);
            ctx.stroke();
            ctx.setLineDash([]);
            
            // Ligne NM
            const pN = toCanvas(data.N.J, data.N.E);
            const pM = toCanvas(data.M.J, data.M.E);
            ctx.beginPath();
            ctx.moveTo(pN.x, pN.y);
            ctx.lineTo(pM.x, pM.y);
            ctx.strokeStyle = '#ff6666';
            ctx.lineWidth = 2;
            ctx.stroke();
            
            // Parallèle à la droite des deux premiers points passant par N
            if (firstTwoPoints) {
                const point1 = firstTwoPoints.point1;
                const slope = (firstTwoPoints.point2.E - point1.E) / (firstTwoPoints.point2.J - point1.J);
                const pPara = toCanvas(maxJ, slope * maxJ + (data.N.E - slope * data.N.J));
                ctx.beginPath();
                ctx.moveTo(pN.x, pN.y);
                ctx.lineTo(pPara.x, pPara.y);
                ctx.strokeStyle = '#ff3333';
                ctx.lineWidth = 2;
                ctx.setLineDash([5, 5]);
                ctx.stroke();
                ctx.setLineDash([]);
            }
            
            // Lignes TS et MS
            const pT = toCanvas(data.T.J, data.T.E);
            const pS = toCanvas(data.S.J, data.S.E);
            
            // TS
            ctx.beginPath();
            ctx.moveTo(pT.x, pT.y);
            ctx.lineTo(pS.x, pS.y);
            ctx.strokeStyle = '#ff6600';
            ctx.lineWidth = 2;
            ctx.setLineDash([3, 3]);
            ctx.stroke();
            ctx.setLineDash([]);
            
            // MS
            ctx.beginPath();
            ctx.moveTo(pM.x, pM.y);
            ctx.lineTo(pS.x, pS.y);
            ctx.strokeStyle = '#ff6600';
            ctx.lineWidth = 2;
            ctx.setLineDash([3, 3]);
            ctx.stroke();
            ctx.setLineDash([]);
            
            // Formules dans le coin supérieur droit
            ctx.fillStyle = '#1a2847';
            ctx.font = '14px IBM Plex Sans';
            ctx.textAlign = 'right';
            ctx.fillText(`α = MS / Id = ${formatNumber(data.alpha, 4)}`, 
                        canvas.width - 20, 40);
            ctx.fillText(`λ = TS / Id = ${formatNumber(data.lambda, 3)} Ω`, 
                        canvas.width - 20, 65);
        }
    }
}

// Fonctions de dessin pour chaque étape de Potier (AJOUTÉES)
function drawPotierStep1(ctx, vacuumData, toCanvas) {
    // Trier les points par J croissant
    const sortedVacuumData = [...vacuumData].sort((a, b) => a.J - b.J);
    
    ctx.beginPath();
    for (let i = 0; i < sortedVacuumData.length; i++) {
        const point = toCanvas(sortedVacuumData[i].J, sortedVacuumData[i].E);
        if (i === 0) ctx.moveTo(point.x, point.y);
        else ctx.lineTo(point.x, point.y);
    }
    ctx.strokeStyle = '#0066cc';
    ctx.lineWidth = 3;
    ctx.stroke();
}

function drawPotierStep2(ctx, data, toCanvas, maxJ, firstTwoPoints) {
    if (!firstTwoPoints) return;
    
    const point1 = firstTwoPoints.point1;
    const point2 = firstTwoPoints.point2;
    const slope = (point2.E - point1.E) / (point2.J - point1.J);
    const intercept = point1.E - slope * point1.J;
    
    // Tracer la droite complète
    const p1 = toCanvas(point1.J, point1.E);
    const p2 = toCanvas(point2.J, point2.E);
    
    // Étendre la droite
    const startJ = Math.max(0, point1.J - 0.5);
    const endJ = Math.min(maxJ, point2.J + 0.5);
    const pStart = toCanvas(startJ, slope * startJ + intercept);
    const pEnd = toCanvas(endJ, slope * endJ + intercept);
    
    ctx.beginPath();
    ctx.moveTo(pStart.x, pStart.y);
    ctx.lineTo(pEnd.x, pEnd.y);
    ctx.strokeStyle = '#ff9900';
    ctx.lineWidth = 2;
    ctx.setLineDash([5, 5]);
    ctx.stroke();
    ctx.setLineDash([]);
    
    // Segment épais entre les points originaux
    ctx.beginPath();
    ctx.moveTo(p1.x, p1.y);
    ctx.lineTo(p2.x, p2.y);
    ctx.strokeStyle = '#ff9900';
    ctx.lineWidth = 4;
    ctx.stroke();
    
    // Marquer les points
    drawPotierPoint(ctx, p1.x, p1.y, '#ff9900', 8);
    drawPotierPoint(ctx, p2.x, p2.y, '#ff9900', 8);
}

function drawPotierStep3(ctx, data, toCanvas) {
    const pM = toCanvas(data.M.J, data.M.E);
    const pMprime = toCanvas(data.Mprime.J, data.Mprime.E);
    
    drawPotierPoint(ctx, pM.x, pM.y, '#00cc66', 6);
    drawPotierPoint(ctx, pMprime.x, pMprime.y, '#cc66ff', 6);
    
    ctx.fillStyle = '#00cc66';
    ctx.font = 'bold 14px IBM Plex Sans';
    ctx.fillText('M', pM.x + 10, pM.y - 10);
    
    ctx.fillStyle = '#cc66ff';
    ctx.fillText("M'", pMprime.x + 10, pMprime.y + 15);
}

function drawPotierStep4(ctx, data, toCanvas) {
    const pM = toCanvas(data.M.J, data.M.E);
    const pN = toCanvas(data.N.J, data.N.E);
    
    drawPotierPoint(ctx, pN.x, pN.y, '#ff6666', 6);
    
    // Ligne NM
    ctx.beginPath();
    ctx.moveTo(pN.x, pN.y);
    ctx.lineTo(pM.x, pM.y);
    ctx.strokeStyle = '#ff6666';
    ctx.lineWidth = 2;
    ctx.stroke();
    
    ctx.fillStyle = '#ff6666';
    ctx.font = 'bold 14px IBM Plex Sans';
    ctx.fillText('N', pN.x - 15, pN.y - 10);
}

function drawPotierStep5(ctx, data, toCanvas, maxJ, firstTwoPoints) {
    if (!firstTwoPoints) return;
    
    const point1 = firstTwoPoints.point1;
    const point2 = firstTwoPoints.point2;
    const slope = (point2.E - point1.E) / (point2.J - point1.J);
    const pN = toCanvas(data.N.J, data.N.E);
    
    // Parallèle passant par N
    const pPara = toCanvas(maxJ, slope * maxJ + (data.N.E - slope * data.N.J));
    
    ctx.beginPath();
    ctx.moveTo(pN.x, pN.y);
    ctx.lineTo(pPara.x, pPara.y);
    ctx.strokeStyle = '#ff3333';
    ctx.lineWidth = 2;
    ctx.setLineDash([5, 5]);
    ctx.stroke();
    ctx.setLineDash([]);
}

function drawPotierStep6(ctx, data, toCanvas) {
    const pT = toCanvas(data.T.J, data.T.E);
    drawPotierPoint(ctx, pT.x, pT.y, '#cc0000', 6);
    
    ctx.fillStyle = '#cc0000';
    ctx.font = 'bold 14px IBM Plex Sans';
    ctx.fillText('T', pT.x + 10, pT.y - 10);
}

function drawPotierStep7(ctx, data, toCanvas) {
    const pT = toCanvas(data.T.J, data.T.E);
    const pS = toCanvas(data.S.J, data.S.E);
    const pM = toCanvas(data.M.J, data.M.E);
    
    drawPotierPoint(ctx, pS.x, pS.y, '#ff6600', 6);
    
    // Segment TS
    ctx.beginPath();
    ctx.moveTo(pT.x, pT.y);
    ctx.lineTo(pS.x, pS.y);
    ctx.strokeStyle = '#ff6600';
    ctx.lineWidth = 2;
    ctx.setLineDash([3, 3]);
    ctx.stroke();
    ctx.setLineDash([]);
    
    // Segment MS
    ctx.beginPath();
    ctx.moveTo(pM.x, pM.y);
    ctx.lineTo(pS.x, pS.y);
    ctx.strokeStyle = '#00cc66';
    ctx.lineWidth = 2;
    ctx.setLineDash([3, 3]);
    ctx.stroke();
    ctx.setLineDash([]);
    
    ctx.fillStyle = '#ff6600';
    ctx.font = 'bold 14px IBM Plex Sans';
    ctx.fillText('S', pS.x + 10, pS.y + 15);
}

function drawPotierGrid(ctx, canvas, margin, width, height, maxJ, maxE) {
    ctx.strokeStyle = 'rgba(0,0,0,0.1)';
    ctx.lineWidth = 0.5;
    
    // Grille verticale (J)
    const stepJ = calculateStep(maxJ);
    for (let J = 0; J <= maxJ; J += stepJ) {
        const x = margin + (J / maxJ) * width;
        ctx.beginPath();
        ctx.moveTo(x, margin);
        ctx.lineTo(x, canvas.height - margin);
        ctx.stroke();
        
        ctx.fillStyle = 'black';
        ctx.font = '12px IBM Plex Sans';
        ctx.fillText(formatNumber(J, 1), x - 10, canvas.height - margin + 20);
    }
    
    // Grille horizontale (E)
    const stepE = calculateStep(maxE);
    for (let E = 0; E <= maxE; E += stepE) {
        const y = canvas.height - margin - (E / maxE) * height;
        ctx.beginPath();
        ctx.moveTo(margin, y);
        ctx.lineTo(canvas.width - margin, y);
        ctx.stroke();
        
        ctx.fillStyle = 'black';
        ctx.font = '12px IBM Plex Sans';
        ctx.fillText(formatNumber(E, 0), margin - 35, y + 4);
    }
}

function drawPotierAxes(ctx, canvas, margin, width, height, maxJ, maxE) {
    // Position de l'origine dans le canvas (bas à gauche)
    const originX = margin;
    const originY = canvas.height - margin;
    
    // Axe des J (horizontal) - de l'origine vers la droite
    const axisEndX = originX + width;
    ctx.beginPath();
    ctx.moveTo(originX, originY);
    ctx.lineTo(axisEndX, originY);
    ctx.strokeStyle = '#000000';
    ctx.lineWidth = 2;
    ctx.stroke();
    
    // Axe des E (vertical) - de l'origine vers le haut
    const axisEndY = originY - height;
    ctx.beginPath();
    ctx.moveTo(originX, originY);
    ctx.lineTo(originX, axisEndY);
    ctx.strokeStyle = '#000000';
    ctx.lineWidth = 2;
    ctx.stroke();
    
    // Flèches
    drawArrow(ctx, axisEndX, originY, 10, 0); // Flèche axe X
    drawArrow(ctx, originX, axisEndY, 10, -Math.PI/2); // Flèche axe Y
    
    // Labels
    ctx.fillStyle = '#000000';
    ctx.font = 'bold 16px IBM Plex Sans';
    ctx.textAlign = 'left';
    ctx.fillText('J (A)', axisEndX + 10, originY - 5);
    ctx.fillText('E (V)', originX - 50, axisEndY - 10);
    
    // Origine
    ctx.fillText('O', originX - 15, originY + 15);
}

/* ================================
   MÉTHODE BEHN-ESCHENBURG (PÔLE LISSE)
=============================== */

function computeBehnEschenburg(type) {
    console.log('Début de computeBehnEschenburg pour', type);
    
    const data = collectData(type);
    
    // Validation
    const errorContainer = document.getElementById(`error-${type}`);
    if (data.caracteristiqueVide.length < 1) {
        showError(errorContainer, "Au moins 1 point de caractéristique à vide est requis");
        return;
    }
    
    if (data.caracteristiqueCC.length < 1) {
        showError(errorContainer, "Au moins 1 point de court-circuit est requis");
        return;
    }
    
    hideError(errorContainer);
    
    // Récupération des données de base
    const Rs = data.rs;
    const V = data.v; // Tension simple
    const I = data.i; // Courant
    const cosphi = data.cosphi;
    const nature = data.nature;
    const mode = data.mode;
    
    // Données des essais
    const vacuumData = data.caracteristiqueVide.map(p => ({ J: p.j, E: p.e }));
    const ccData = data.caracteristiqueCC.map(p => ({ J: p.jcc, Icc: p.icc }));
    
    // 1. Détermination de Xs et K
    // Pour Behn-Eschenburg, on prend la pente entre les deux premiers points
    const slope = calculateVacuumSlopeFirstTwoPoints(vacuumData);
    const K = slope; // Constante machine (E/J dans la zone linéaire)
    
    // Pour le point de court-circuit, on prend le premier point
    const ccPoint = ccData[0];
    const Ecc = K * ccPoint.J;
    const Zs = Ecc / ccPoint.Icc;
    const Xs = Math.sqrt(Math.pow(Zs, 2) - Math.pow(Rs, 2));
    
    // 2. Calcul des grandeurs
    const phi = Math.acos(cosphi);
    let phiAdjusted = phi;
    
    // Ajustement du signe de phi selon la nature de la charge et le mode
    if (nature === 'inductive') {
        phiAdjusted = (mode === 'generatrice') ? -phi : phi;
    } else if (nature === 'capacitive') {
        phiAdjusted = (mode === 'generatrice') ? phi : -phi;
    } else {
        phiAdjusted = 0;
    }
    
    // Composantes
    const Vx = V;
    const Vy = 0;
    
    const Ix = I * Math.cos(phiAdjusted);
    const Iy = I * Math.sin(phiAdjusted);
    
    // Chutes de tension
    const RIx = Rs * Ix;
    const RIy = Rs * Iy;
    
    const XIx = -Xs * Iy;
    const XIy = Xs * Ix;
    
    // FEM E selon le mode
    let Ex, Ey;
    if (mode === "generatrice") {
        Ex = Vx + RIx + XIx;
        Ey = Vy + RIy + XIy;
    } else { // moteur
        Ex = Vx + RIx - XIx;
        Ey = Vy + RIy - XIy;
    }
    
    const E = Math.sqrt(Ex * Ex + Ey * Ey);
    const delta = Math.atan2(Ey, Ex) * 180 / Math.PI;
    
    // Courant d'excitation J (linéaire)
    const J = E / K;
    
    // Régulation de tension
    const VR = ((E - V) / V) * 100;
    
    // Stocker pour l'affichage ultérieur
    lastComputedData[type] = {
        type: 'behn',
        results: {
            V: { x: Vx, y: Vy },
            I: { x: Ix, y: Iy },
            RI: { x: RIx, y: RIy },
            XI: { x: XIx, y: XIy },
            E: { x: Ex, y: Ey },
            mode: mode,
            nature: nature,
            delta: delta,
            V_phase: V,
            I_phase: I,
            E_value: E,
            delta_value: delta,
            J_value: J,
            VR: VR,
            Xs: Xs,
            K: K,
            mode_text: mode === "generatrice" ? "Génératrice" : "Moteur",
            nature_text: nature === "inductive" ? "Inductive" : 
                   nature === "capacitive" ? "Capacitive" : "Résistive",
            phiAdjusted: phiAdjusted
        }
    };
    
    // Affichage des résultats (sans J)
    displayBehnResults(type, {
        V_phase: V,
        I_phase: I,
        E: E,
        delta: delta,
        VR: VR,
        Xs: Xs,
        K: K,
        mode: mode === "generatrice" ? "Génératrice" : "Moteur",
        nature: nature === "inductive" ? "Inductive" : 
               nature === "capacitive" ? "Capacitive" : "Résistive"
    });
    
    // Dessin du diagramme
    drawBehnDiagram(type, lastComputedData[type].results);
}

function displayBehnResults(type, results) {
    const outputsContainer = document.getElementById(`outputs-${type}`);
    
    if (!outputsContainer) {
        console.error(`Container outputs-${type} non trouvé`);
        return;
    }
    
    outputsContainer.innerHTML = `
      
        <div class="output-item">
            <div class="output-label">FEM interne E</div>
            <div class="output-value">${formatNumber(results.E, 2)} V</div>
        </div>
        <div class="output-item">
            <div class="output-label">Angle de charge δ</div>
            <div class="output-value">${formatNumber(results.delta, 2)}°</div>
        </div>
        
        <div class="output-item">
            <div class="output-label">Réactance synchrone Xs</div>
            <div class="output-value">${formatNumber(results.Xs, 3)} Ω</div>
        </div>
        
    `;
}

function drawBehnDiagram(type, data, currentAnimationStep = -1) {
    const canvas = document.getElementById(`diagramCanvas-${type}`);
    if (!canvas) {
        console.error(`Canvas non trouvé pour ${type}`);
        return;
    }
    
    const ctx = canvas.getContext('2d');
    
    // Taille du canvas
    canvas.width = canvas.parentElement.clientWidth - 4;
    canvas.height = canvas.parentElement.clientHeight - 4;
    
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Vérifier les données
    const allPoints = [
        data.V, data.I, data.E,
        { x: 0, y: 0 },
        { x: data.V.x + data.RI.x, y: data.RI.y },
        { x: data.V.x + data.RI.x + data.XI.x, y: data.RI.y + data.XI.y }
    ];
    
    if (!hasValidData(allPoints)) {
        ctx.fillStyle = '#666';
        ctx.font = '20px IBM Plex Sans';
        ctx.textAlign = 'center';
        ctx.fillText('Pas de données valides à afficher', canvas.width/2, canvas.height/2);
        setDiagramTitle(type, 'Diagramme de Behn-Eschenburg - Données manquantes');
        return;
    }
    
    // Définir le titre
    setDiagramTitle(type, 'Diagramme de Behn-Eschenburg');
    
    // Calculer les limites
    const maxX = Math.max(
        Math.abs(data.V.x),
        Math.abs(data.I.x),
        Math.abs(data.E.x),
        Math.abs(data.V.x + data.RI.x + data.XI.x),
        50
    ) * 1.2;
    
    const maxY = Math.max(
        Math.abs(data.I.y),
        Math.abs(data.E.y),
        Math.abs(data.RI.y + data.XI.y),
        50
    ) * 1.2;
    
    // Marges
    const margin = 80;
    const graphWidth = canvas.width - 2 * margin;
    const graphHeight = canvas.height - 2 * margin;
    
    const scaleX = graphWidth / maxX;
    const scaleY = graphHeight / maxY;
    const scale = Math.min(scaleX, scaleY);
    
    // Origine au centre gauche
    const originX = margin;
    const originY = canvas.height - margin;
    
    // Fonction de conversion
    const toCanvas = (x, y) => ({
        x: originX + x * scale,
        y: originY - y * scale
    });
    
    // Dessiner la grille
    drawBehnGrid(ctx, canvas, originX, originY, scale, maxX, maxY);
    
    // Dessiner les axes
    drawBehnAxes(ctx, canvas, originX, originY, scale, maxX, maxY);
    
    // Récupérer les éléments visibles
    const visibleElements = currentVisibleLisse.behn;
    
    // Vecteurs avec leurs propriétés
    const vectors = [
        { name: 'V', start: toCanvas(0, 0), end: toCanvas(data.V.x, data.V.y), color: '#2196F3', label: 'V' },
        { name: 'I', start: toCanvas(0, 0), end: toCanvas(data.I.x, data.I.y), color: '#4CAF50', label: 'I' },
        { name: 'RsI', start: toCanvas(data.V.x, data.V.y), 
          end: toCanvas(data.V.x + data.RI.x, data.V.y + data.RI.y), 
          color: '#FF9800', label: 'Rs·I' },
        { name: 'XsI', start: toCanvas(data.V.x + data.RI.x, data.V.y + data.RI.y),
          end: toCanvas(data.V.x + data.RI.x + data.XI.x, data.V.y + data.RI.y + data.XI.y),
          color: '#9C27B0', label: 'jXs·I' },
        { name: 'E', start: toCanvas(0, 0), end: toCanvas(data.E.x, data.E.y), color: '#F44336', label: 'E' }
    ];
    
    if (currentAnimationStep >= 0 && isAnimatingLisse) {
        // Mode animation - dessiner les vecteurs un par un
        for (let i = 0; i <= currentAnimationStep; i++) {
            const vector = vectors[i];
            if (vector && visibleElements[vector.name]) {
                drawVector(ctx, vector.start.x, vector.start.y, vector.end.x, vector.end.y, vector.color, vector.label);
            }
        }
    } else {
        // Mode normal - dessiner tous les vecteurs visibles
        vectors.forEach(vec => {
            if (visibleElements[vec.name]) {
                drawVector(ctx, vec.start.x, vec.start.y, vec.end.x, vec.end.y, vec.color, vec.label);
            }
        });
    }
}

function drawBehnGrid(ctx, canvas, originX, originY, scale, maxX, maxY) {
    ctx.strokeStyle = 'rgba(0,0,0,0.1)';
    ctx.lineWidth = 0.5;
    
    // Grille verticale
    const stepX = calculateStep(maxX);
    for (let x = 0; x <= maxX; x += stepX) {
        const canvasX = originX + x * scale;
        ctx.beginPath();
        ctx.moveTo(canvasX, originY - maxY * scale * 1.1);
        ctx.lineTo(canvasX, originY + maxY * scale * 0.1);
        ctx.stroke();
        
        ctx.fillStyle = 'black';
        ctx.font = '12px IBM Plex Sans';
        ctx.fillText(formatNumber(x, 1), canvasX - 10, originY + 20);
    }
    
    // Grille horizontale
    const stepY = calculateStep(maxY);
    for (let y = -Math.floor(maxY/stepY)*stepY; y <= maxY; y += stepY) {
        const canvasY = originY - y * scale;
        ctx.beginPath();
        ctx.moveTo(originX - maxX * scale * 0.1, canvasY);
        ctx.lineTo(originX + maxX * scale * 1.1, canvasY);
        ctx.stroke();
        
        if (Math.abs(y) > 0.01) {
            ctx.fillStyle = 'black';
            ctx.font = '12px IBM Plex Sans';
            ctx.fillText(formatNumber(y, 1), originX - 40, canvasY + 4);
        }
    }
}

function drawBehnAxes(ctx, canvas, originX, originY, scale, maxX, maxY) {
    // Axe X (horizontal)
    ctx.beginPath();
    ctx.moveTo(originX - maxX * scale * 0.1, originY);
    ctx.lineTo(originX + maxX * scale * 1.1, originY);
    ctx.strokeStyle = '#000000';
    ctx.lineWidth = 2;
    ctx.stroke();
    
    // Axe Y (vertical)
    ctx.beginPath();
    ctx.moveTo(originX, originY + maxY * scale * 0.1);
    ctx.lineTo(originX, originY - maxY * scale * 1.1);
    ctx.strokeStyle = '#000000';
    ctx.lineWidth = 2;
    ctx.stroke();
    
    // Flèches
    drawArrow(ctx, originX + maxX * scale * 1.1, originY, 10, 0);
    drawArrow(ctx, originX, originY - maxY * scale * 1.1, 10, -Math.PI/2);
    
    // Labels
    ctx.fillStyle = '#000000';
    ctx.font = 'bold 14px IBM Plex Sans';
    ctx.fillText('Réel', originX + maxX * scale * 1.1 + 10, originY - 5);
    ctx.fillText('Imaginaire', originX + 10, originY - maxY * scale * 1.1 - 10);
    
    // Origine
    ctx.fillText('O', originX - 15, originY + 15);
}

/* ================================
   NOUVELLE FONCTION: Calcul du courant d'excitation J pour pôle lisse
=============================== */

function calculerCourantExcitationJLisse() {
    const type = 'lisse';
    const computedData = lastComputedData[type];
    
    if (!computedData) {
        alert("Veuillez d'abord générer un diagramme (Potier ou Behn-Eschenburg).");
        return;
    }
    
    const cadreCourantJ = document.getElementById('cadre-courant-J-lisse');
    cadreCourantJ.style.display = 'block';
    
    if (computedData.type === 'potier') {
        const results = computedData.results;
        
        const calculEtapes = document.getElementById('calcul-etapes-lisse');
        calculEtapes.innerHTML = `
            <div class="etape-calcul">
                <div class="etape-label">1. Calcul de l'angle φ :</div>
                <div class="etape-valeur">φ = ${results.nature === 'inductive' ? '+' : results.nature === 'capacitive' ? '-' : ''}arccos(${Math.cos(results.phi).toFixed(3)}) = ${results.phiDeg.toFixed(2)}°</div>
            </div>
            <div class="etape-calcul">
                <div class="etape-label">2. Calcul de Er (force électromotrice réaction) :</div>
                <div class="etape-valeur">Er = √[(V·cosφ + Rs·I)² + (V·sinφ + λ·I)²]</div>
                <div class="etape-valeur">Er = √[(${results.V.toFixed(2)}·${Math.cos(results.phi).toFixed(3)} + ${results.Rs.toFixed(2)}·${results.I.toFixed(2)})² + (${results.V.toFixed(2)}·${Math.sin(results.phi).toFixed(3)} + ${results.lambda.toFixed(3)}·${results.I.toFixed(2)})²] = ${results.Er.toFixed(2)} V</div>
            </div>
            <div class="etape-calcul">
                <div class="etape-label">3. Détermination de Jr à partir de la caractéristique à vide :</div>
                <div class="etape-valeur">Pour Er = ${results.Er.toFixed(2)} V → Jr = ${results.Jr.toFixed(2)} A (par interpolation)</div>
            </div>
            <div class="etape-calcul">
                <div class="etape-label">4. Calcul du courant d'excitation total J :</div>
                <div class="etape-valeur">J = Jr + α·I = ${results.Jr.toFixed(2)} + ${results.alpha.toFixed(4)}·${results.I.toFixed(2)}</div>
                <div class="etape-valeur">J = ${results.Jr.toFixed(2)} + ${(results.alpha * results.I).toFixed(2)} = ${results.J_excitation.toFixed(2)} A</div>
            </div>
        `;
        
        document.getElementById('valeur-courant-J-lisse').textContent = `${results.J_excitation.toFixed(2)} A`;
        
    } else if (computedData.type === 'behn') {
        const results = computedData.results;
        
        const calculEtapes = document.getElementById('calcul-etapes-lisse');
        calculEtapes.innerHTML = `
            <div class="etape-calcul">
                <div class="etape-label">1. Calcul de la constante K (pente entre les deux premiers points) :</div>
                <div class="etape-valeur">K = (E₂ - E₁)/(J₂ - J₁) = ${results.K.toFixed(2)} V/A</div>
            </div>
            <div class="etape-calcul">
                <div class="etape-label">2. Calcul de la FEM interne E :</div>
                <div class="etape-valeur">E = √[(V + Rs·I·cosφ ± Xs·I·sinφ)² + (Rs·I·sinφ ∓ Xs·I·cosφ)²]</div>
                <div class="etape-valeur">E = ${results.E_value.toFixed(2)} V</div>
            </div>
            <div class="etape-calcul">
                <div class="etape-label">3. Calcul du courant d'excitation J (linéaire) :</div>
                <div class="etape-valeur">J = E / K = ${results.E_value.toFixed(2)} / ${results.K.toFixed(2)}</div>
                <div class="etape-valeur">J = ${results.J_value.toFixed(2)} A</div>
            </div>
            <div class="etape-calcul">
                <div class="etape-label">4. Vérification de la régulation de tension :</div>
                <div class="etape-valeur">VR = ((E - V) / V) × 100 = ${results.VR.toFixed(2)} %</div>
            </div>
        `;
        
        document.getElementById('valeur-courant-J-lisse').textContent = `${results.J_value.toFixed(2)} A`;
    }
    
    cadreCourantJ.scrollIntoView({ behavior: 'smooth' });
}

// Initialisation
document.addEventListener('DOMContentLoaded', function() {
    setupMachineTypeListeners();
});