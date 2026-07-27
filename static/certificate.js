// ==========================================
// 🛠️ لوحة التحكم في المقاسات والألوان 🛠️
// ==========================================
const CERT_SETTINGS = {
    // 1. إعدادات شهادة التميز (الأوائل)
    top: {
        name:  { y: 0.43, size: 110, color: '#991b1b' }, // الاسم
        line1: { y: 0.54, size: 36, color: '#334155' },  // سطر "لتفوقه الدراسي..."
        rank:  { y: 0.60, size: 60, color: '#b48608' },  // سطر "المركز..."
        score: { y: 0.66, textSize: 40, numSize: 44, textColor: '#334155', numColor: '#991b1b' }, // سطر المجموع
        date:  { x: 0.695, y: 0.78, size: 32, color: '#1e293b' } // التاريخ
    },

    // 2. إعدادات الشهادة العادية
    normal: {
        name:  { y: 0.38, size: 130, color: '#991b1b' }, // الاسم
        line1: { y: 0.54, size: 40, netigatySize: 45, textColor: '#334155', netigatyColor: '#991b1b' }, // سطر "تتقدم منصة نتيجتي..."
        line2: { y: 0.62, size: 42, numSize: 46, textColor: '#334155', numColor: '#991b1b' }, // سطر المجموع
        line3: { y: 0.69, size: 36, color: '#334155' }, // سطر "متمنين له دوام التميز..."
        date:  { x: 0.765, y: 0.79, size: 34, color: '#1e293b' } // التاريخ
    }
};

// ==========================================
// المسارات الأساسية
// ==========================================
const TOP_CERT_IMG = "/static/top_cert_2.jpg"; 
const NORMAL_CERT_IMG = "/static/normal_cert_2.jpg"; 
const CUSTOM_FONT_URL = "/static/thuluth.ttf"; 

let isFontLoaded = false;

async function loadFonts() {
    if(isFontLoaded) return;
    try {
        const thuluthFont = new FontFace('CustomThuluth', `url(${CUSTOM_FONT_URL})`);
        const cairoFont = new FontFace('Cairo', 'url(https://fonts.gstatic.com/s/cairo/v28/SLXWc1nY6Hkvalv7as1G.woff2)', { weight: '700' });
        
        await Promise.all([thuluthFont.load(), cairoFont.load()]);
        document.fonts.add(thuluthFont);
        document.fonts.add(cairoFont);
        
        const hiddenDiv = document.createElement('div');
        hiddenDiv.style.fontFamily = 'CustomThuluth, Cairo';
        hiddenDiv.style.opacity = '0';
        hiddenDiv.style.position = 'absolute';
        hiddenDiv.innerHTML = 'تفعيل الخط';
        document.body.appendChild(hiddenDiv);
        
        await document.fonts.ready; 
        await new Promise(resolve => setTimeout(resolve, 150));
        isFontLoaded = true;
    } catch(e) {
        console.error("Font Error:", e);
    }
}

function loadImage(src) {
    return new Promise((resolve, reject) => {
        const img = new Image();
        img.src = src;
        img.onload = () => resolve(img);
        img.onerror = () => resolve(null); 
    });
}

function drawRichText(ctx, segments, y, centerX) {
    ctx.save();
    ctx.direction = 'rtl';
    ctx.textAlign = 'right';
    
    let totalWidth = 0;
    const widths = [];
    
    segments.forEach(seg => {
        if (seg.font) ctx.font = seg.font;
        let w = ctx.measureText(seg.text).width;
        widths.push(w);
        totalWidth += w;
    });
    
    let currentX = centerX + (totalWidth / 2);
    
    segments.forEach((seg, i) => {
        if (seg.font) ctx.font = seg.font;
        ctx.fillStyle = seg.color;
        ctx.fillText(seg.text, currentX, y);
        currentX -= widths[i]; 
    });
    
    ctx.restore();
}

async function previewCertificate() {
    if (!window.currentModalStudent) return;
    
    const student = window.currentModalStudent;
    const btn = document.getElementById('viewCertBtnTop');
    const originalIcon = btn.innerHTML;
    
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
    btn.disabled = true;

    try {
        await loadFonts();

        const previewModal = document.getElementById('certPreviewModal');
        const previewContent = document.getElementById('certPreviewContent');
        previewModal.classList.remove('hidden');
        previewModal.classList.add('flex');
        setTimeout(() => {
            previewModal.classList.remove('opacity-0');
            previewContent.classList.remove('scale-95');
        }, 10);

        let rSchool = parseInt(document.getElementById('rankSchool').innerText) || 999;
        let rAdmin = parseInt(document.getElementById('rankAdmin').innerText) || 999;
        let rGov = parseInt(document.getElementById('rankGov').innerText) || 999;
        let totalScore = student['مجموع كلى'];
        let percentage = document.getElementById('modalPercentage').innerText;

        let isTopStudent = (rSchool <= 10 || rAdmin <= 10 || rGov <= 10);

        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');

        const bgImgSrc = isTopStudent ? TOP_CERT_IMG : NORMAL_CERT_IMG;
        const bgImg = await loadImage(bgImgSrc);
        
        if (!bgImg) {
            alert("تعذر العثور على صورة الشهادة!");
            throw new Error("Background image missing");
        }

        canvas.width = bgImg.width;
        canvas.height = bgImg.height;
        ctx.drawImage(bgImg, 0, 0, canvas.width, canvas.height);

        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.direction = 'rtl'; 

        const centerX = canvas.width / 2;
        const maxNameWidth = canvas.width * 0.85; 
        
        let today = new Date();
        let dateString = today.toLocaleDateString('ar-EG');

        // تنشيط الخط المخصص
        ctx.font = '10px "CustomThuluth"';
        ctx.fillText(' ', 0, 0);

        if (isTopStudent) {
            // ==========================================
            // تطبيق إعدادات شهادة التميز من لوحة التحكم
            // ==========================================
            const cfg = CERT_SETTINGS.top;

            let bestRankText = '';
            if (rGov <= 10) bestRankText = `المركز ${rGov} على المحافظة`;
            else if (rAdmin <= 10) bestRankText = `المركز ${rAdmin} على الإدارة`;
            else bestRankText = `المركز ${rSchool} على المدرسة`;

            ctx.font = `${cfg.name.size}px "CustomThuluth", "Amiri", serif`;
            ctx.fillStyle = cfg.name.color; 
            ctx.fillText(student['اسم الطالب'], centerX, canvas.height * cfg.name.y, maxNameWidth);

            ctx.font = `bold ${cfg.line1.size}px "Cairo", sans-serif`;
            ctx.fillStyle = cfg.line1.color; 
            ctx.fillText('لتفوقه(ا) الدراسي الباهر وتحقيقه(ا) إنجازاً استثنائياً يبعث على الفخر والاعتزاز، بحصد', centerX, canvas.height * cfg.line1.y);
            
            ctx.font = `900 ${cfg.rank.size}px "Cairo", sans-serif`;
            ctx.fillStyle = cfg.rank.color; 
            ctx.fillText(bestRankText, centerX, canvas.height * cfg.rank.y);

            const topScoreLine = [
                { text: 'بمجموع ', color: cfg.score.textColor, font: `bold ${cfg.score.textSize}px "Cairo", sans-serif` },
                { text: `${totalScore}`, color: cfg.score.numColor, font: `900 ${cfg.score.numSize}px "Cairo", sans-serif` },
                { text: ' درجة ونسبة ', color: cfg.score.textColor, font: `bold ${cfg.score.textSize}px "Cairo", sans-serif` },
                { text: `${percentage}`, color: cfg.score.numColor, font: `900 ${cfg.score.numSize}px "Cairo", sans-serif` }
            ];
            drawRichText(ctx, topScoreLine, canvas.height * cfg.score.y, centerX);

            ctx.font = `bold ${cfg.date.size}px "Cairo", sans-serif`;
            ctx.fillStyle = cfg.date.color; 
            ctx.fillText(dateString, canvas.width * cfg.date.x, canvas.height * cfg.date.y);

        } else {
            // ==========================================
            // تطبيق إعدادات الشهادة العادية من لوحة التحكم
            // ==========================================
            const cfg = CERT_SETTINGS.normal;

            ctx.font = `${cfg.name.size}px "CustomThuluth", "Amiri", serif`;
            ctx.fillStyle = cfg.name.color; 
            ctx.fillText(student['اسم الطالب'], centerX, canvas.height * cfg.name.y, maxNameWidth); 

            const line1 = [
                { text: 'تتقدم إدارة منصة ', color: cfg.line1.textColor, font: `bold ${cfg.line1.size}px "Cairo", sans-serif` },
                { text: 'نتيجتي', color: cfg.line1.netigatyColor, font: `900 ${cfg.line1.netigatySize}px "Cairo", sans-serif` },
                { text: ' بخالص التهنئة لاجتيازه(ا) امتحانات الشهادة الإعدادية بتفوق،', color: cfg.line1.textColor, font: `bold ${cfg.line1.size}px "Cairo", sans-serif` }
            ];
            drawRichText(ctx, line1, canvas.height * cfg.line1.y, centerX);
            
            const line2 = [
                { text: 'وحصوله(ا) على مجموع ', color: cfg.line2.textColor, font: `bold ${cfg.line2.size}px "Cairo", sans-serif` },
                { text: `${totalScore}`, color: cfg.line2.numColor, font: `900 ${cfg.line2.numSize}px "Cairo", sans-serif` },
                { text: ' بنسبة ', color: cfg.line2.textColor, font: `bold ${cfg.line2.size}px "Cairo", sans-serif` },
                { text: `${percentage}`, color: cfg.line2.numColor, font: `900 ${cfg.line2.numSize}px "Cairo", sans-serif` }
            ];
            drawRichText(ctx, line2, canvas.height * cfg.line2.y, centerX);
            
            ctx.font = `bold ${cfg.line3.size}px "Cairo", sans-serif`;
            ctx.fillStyle = cfg.line3.color;
            ctx.fillText('متمنين له(ا) دوام التميز والإبداع في مسيرته(ا) العلمية.', centerX, canvas.height * cfg.line3.y);

            ctx.font = `bold ${cfg.date.size}px "Cairo", sans-serif`;
            ctx.fillStyle = cfg.date.color; 
            ctx.fillText(dateString, canvas.width * cfg.date.x, canvas.height * cfg.date.y);
        }

        const dataUrl = canvas.toDataURL('image/jpeg', 1.0); 
        const imgElement = document.getElementById('certPreviewImage');
        
        imgElement.src = dataUrl;
        document.getElementById('certLoading').classList.add('hidden');
        imgElement.classList.remove('hidden');

    } catch (error) {
        console.error(error);
        closeCertPreview();
    } finally {
        btn.innerHTML = originalIcon;
        btn.disabled = false;
    }
}

function downloadActualCertificate() {
    if (!window.currentModalStudent) return;
    
    const imgSrc = document.getElementById('certPreviewImage').src;
    if (!imgSrc || imgSrc === "") return;

    const link = document.createElement('a');
    link.download = `شهادة_${window.currentModalStudent['رقم الجلوس']}.jpg`;
    link.href = imgSrc;
    link.click();
}

function closeCertPreview() {
    const modal = document.getElementById('certPreviewModal');
    const content = document.getElementById('certPreviewContent');
    modal.classList.add('opacity-0');
    content.classList.add('scale-95');
    setTimeout(() => { 
        modal.classList.add('hidden'); 
        modal.classList.remove('flex');
    }, 300);
    
    setTimeout(() => {
        document.getElementById('certPreviewImage').src = "";
        document.getElementById('certPreviewImage').classList.add('hidden');
        document.getElementById('certLoading').classList.remove('hidden');
    }, 300);
}