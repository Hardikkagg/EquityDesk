document.addEventListener('DOMContentLoaded', () => {
    const state = {
        investors: [],
        portfolios: [],
        securities: [],
        holdings: [],
        trades: [],
        analytics: null,
        market: null,
        selectedInvestorId: '',
        selectedPortfolioId: '',
        investorContextLoading: false,
        currentPage: 'market',
        selectedInvestor: null,
        securityDetailId: null,
        securityHistoryPeriod: '1M',
        portfolioDetailId: null,
        watchlist: [],
        investorHoldings: [],
        investorTrades: [],
        marketSecurities: [],
        refreshSequence: 0,
        sellCheckSequence: 0,
    };

    const byId = (id) => document.getElementById(id);
    const elements = {
        sidebar: byId('sidebar'),
        statusDot: byId('status-dot'),
        backendStatus: byId('backend-status-text'),
        databaseStatus: byId('database-status-text'),
        toast: byId('notification-banner'),
        pageTitle: byId('page-title'),
        pageEyebrow: byId('page-eyebrow'),
        investorFilter: byId('investor-filter'),
        portfolioFilter: byId('global-portfolio-filter'),
        globalSearch: byId('global-search'),
        marketSearch: byId('market-search'),
        marketSector: byId('market-sector'),
        marketMinPrice: byId('market-min-price'),
        marketMaxPrice: byId('market-max-price'),
        marketSort: byId('market-sort'),
        holdingsSearch: byId('holdings-search'),
        holdingsSector: byId('holdings-sector'),
        holdingsSort: byId('holdings-sort'),
        holdingsGroupToggle: byId('holdings-group-toggle'),
        securitySearch: byId('security-search'),
        securitySector: byId('security-sector'),
        securityMinPrice: byId('security-min-price'),
        securityMaxPrice: byId('security-max-price'),
        securitySort: byId('security-sort'),
        tradeTypeFilter: byId('trade-type-filter'),
        tradeStatusFilter: byId('trade-status-filter'),
        tradePortfolioFilter: byId('trade-portfolio-filter'),
        tradeSecurityFilter: byId('trade-security-filter'),
        tradeSearch: byId('trade-search'),
        tradeFromDate: byId('trade-from-date'),
        tradeToDate: byId('trade-to-date'),
        tradeForm: byId('trade-form'),
        formInvestor: byId('form-investor'),
        formPortfolio: byId('form-portfolio'),
        formSecurity: byId('form-security'),
        formQuantity: byId('form-quantity'),
        formPrice: byId('form-price'),
        formDate: byId('form-date'),
        tradeEstimate: byId('trade-total-estimate'),
        tradeFormError: byId('trade-form-error'),
        portfolioModal: byId('portfolio-modal'),
        portfolioForm: byId('portfolio-form'),
        portfolioInvestor: byId('portfolio-investor'),
        portfolioInvestorField: byId('portfolio-investor-field'),
        portfolioName: byId('portfolio-name'),
        portfolioId: byId('portfolio-id'),
        portfolioModalTitle: byId('portfolio-modal-title'),
        savePortfolioButton: byId('save-portfolio-button'),
        securityModal: byId('security-modal'),
        securityModalTitle: byId('security-modal-title'),
        securityModalContent: byId('security-modal-content'),
        securityWatchlistButton: byId('security-watchlist-button'),
        voidTradeModal: byId('void-trade-modal'),
        voidTradeForm: byId('void-trade-form'),
        voidTradeId: byId('void-trade-id'),
        voidTradeReason: byId('void-trade-reason'),
        confirmVoidButton: byId('confirm-void-button'),
        watchlistSearch: byId('watchlist-search'),
        watchlistSector: byId('watchlist-sector'),
        investorSearch: byId('investor-search'),
        portfolioSearch: byId('portfolio-search'),
        portfolioSort: byId('portfolio-sort'),
        securityDetailWatchlist: byId('security-detail-watchlist'),
    };

    const pageCopy = {
        market: ['Market Discover', 'EXPLORE THE MARKET'],
        'portfolio-overview': ['Portfolio overview', 'YOUR FINANCIAL OVERVIEW'],
        investors: ['Investors', 'INVESTOR DIRECTORY'],
        'investor-workspace': ['Investor workspace', 'INDIVIDUAL INVESTOR'],
        portfolios: ['Portfolios', 'ORGANIZE YOUR INVESTMENTS'],
        holdings: ['Holdings', 'EVERY POSITION, AT A GLANCE'],
        securities: ['Securities', 'EXPLORE YOUR INVESTABLE UNIVERSE'],
        'security-detail': ['Security details', 'SECURITY PROFILE'],
        'portfolio-detail': ['Portfolio details', 'PORTFOLIO WORKSPACE'],
        transactions: ['Transactions', 'YOUR COMPLETE ORDER HISTORY'],
        watchlist: ['Watchlist', 'KEEP AN EYE ON SECURITIES'],
        analytics: ['Analytics', 'UNDERSTAND YOUR PORTFOLIO'],
        risk: ['Risk & allocation', 'A RULE-BASED PORTFOLIO CHECK'],
    };
    const chartColors = ['#9ee5ad', '#83b9ad', '#8e9ae0', '#dfb66f', '#c18bd1', '#79a7da', '#de8b86'];
    const demoMarket = {
        indices: [
            { name: 'NIFTY 50', value: '24,386.70', change: 164.25, percent: 0.68 },
            { name: 'SENSEX', value: '80,142.35', change: 512.80, percent: 0.64 },
            { name: 'BANK NIFTY', value: '52,870.20', change: -118.40, percent: -0.22 },
        ],
        gainers: [
            { symbol: 'NOVAFOOD', name: 'Nova Foods Ltd.', sector: 'Consumer Staples', price: 842.6, change: 5.84 },
            { symbol: 'ORBITAL', name: 'Orbital Mobility', sector: 'Automotive', price: 1264.3, change: 4.12 },
            { symbol: 'GREENGRID', name: 'GreenGrid Energy', sector: 'Clean Energy', price: 388.75, change: 3.67 },
        ],
        losers: [
            { symbol: 'CLOUDNINE', name: 'CloudNine Systems', sector: 'Technology', price: 972.4, change: -4.38 },
            { symbol: 'NORTHSTAR', name: 'Northstar Metals', sector: 'Metals', price: 614.8, change: -3.21 },
            { symbol: 'BLUEHARBOR', name: 'BlueHarbor Finance', sector: 'Financials', price: 458.9, change: -2.74 },
        ],
        traded: [
            { symbol: 'VISTABANK', name: 'Vista Bank', sector: 'Banking', price: 1184.5, change: 0.82, volume: '18.4M' },
            { symbol: 'ARCADIA', name: 'Arcadia Telecom', sector: 'Telecom', price: 326.2, change: -0.36, volume: '15.1M' },
            { symbol: 'SOLSTICE', name: 'Solstice Pharma', sector: 'Healthcare', price: 754.8, change: 1.15, volume: '12.8M' },
        ],
        intraday: [
            { symbol: 'RIVERSTONE', name: 'Riverstone Infra', sector: 'Infrastructure', price: 519.65, change: 1.42, volume: '9.6M' },
            { symbol: 'AURORATECH', name: 'Aurora Technologies', sector: 'Technology', price: 1432.8, change: 2.08, volume: '8.3M' },
            { symbol: 'CROWNRETAIL', name: 'Crown Retail', sector: 'Retail', price: 286.35, change: -0.74, volume: '7.9M' },
        ],
        mtf: [
            { symbol: 'ZENITHAUTO', name: 'Zenith Auto', sector: 'Automotive', price: 1048.25, change: 1.24, volume: '6.2M' },
            { symbol: 'PEAKCEMENT', name: 'Peak Cement', sector: 'Materials', price: 392.7, change: -0.48, volume: '4.8M' },
            { symbol: 'LUMENIND', name: 'Lumen Industries', sector: 'Industrials', price: 865.1, change: 0.93, volume: '4.1M' },
        ],
        shockers: [
            { symbol: 'EASTWIND', name: 'Eastwind Logistics', sector: 'Logistics', price: 271.4, change: 2.81, volume: '3.2× avg.' },
            { symbol: 'SILVERLINE', name: 'Silverline Cables', sector: 'Industrials', price: 438.6, change: -1.12, volume: '2.7× avg.' },
            { symbol: 'MINTLEAF', name: 'Mintleaf Consumer', sector: 'Consumer', price: 196.8, change: 1.76, volume: '2.3× avg.' },
        ],
        sectors: [
            { name: 'Consumer Staples', change: 1.28 },
            { name: 'Information Technology', change: 0.86 },
            { name: 'Banking', change: 0.42 },
            { name: 'Energy', change: -0.31 },
            { name: 'Metals', change: -0.77 },
            { name: 'Healthcare', change: 0.64 },
        ],
        etfs: [
            { symbol: 'DEMO50', name: 'Demo Nifty 50 ETF', sector: 'Index ETF', price: 248.6, change: 0.61, volume: '1.8M' },
            { symbol: 'DEMO-BANK', name: 'Demo Banking ETF', sector: 'Sector ETF', price: 116.35, change: 0.28, volume: '1.2M' },
            { symbol: 'DEMO-GREEN', name: 'Demo Green Energy ETF', sector: 'Thematic ETF', price: 82.4, change: 1.04, volume: '0.9M' },
        ],
        global: [
            { symbol: 'NVDA', name: 'Nvidia · demo quote', sector: 'Technology', price: 142.6, change: 1.38, currency: 'USD' },
            { symbol: 'MSFT', name: 'Microsoft · demo quote', sector: 'Technology', price: 428.15, change: 0.42, currency: 'USD' },
            { symbol: 'SPY', name: 'S&P 500 ETF · demo quote', sector: 'Index ETF', price: 592.8, change: -0.16, currency: 'USD' },
        ],
        news: [
            { symbol: 'NOVAFOOD', headline: 'Nova Foods outlines a fictional expansion of its regional distribution network.', time: 'DEMO STORY · 10:25' },
            { symbol: 'AURORATECH', headline: 'Aurora Technologies announces a fictional research investment update.', time: 'DEMO STORY · 09:40' },
            { symbol: 'VISTABANK', headline: 'Vista Bank presents a fictional digital services roadmap.', time: 'DEMO STORY · YESTERDAY' },
        ],
    };
    let toastTimer;
    let holdingsTimer;
    let securityTimer;

    function escapeHtml(value) {
        return String(value ?? '').replace(/[&<>"']/g, (character) => ({
            '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
        })[character]);
    }

    function currency(value, compact = false) {
        const amount = Number(value) || 0;
        if (compact && Math.abs(amount) >= 10000000) {
            return `₹${(amount / 10000000).toFixed(1)}Cr`;
        }
        if (compact && Math.abs(amount) >= 100000) {
            return `₹${(amount / 100000).toFixed(1)}L`;
        }
        return `₹${amount.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    }

    function signed(value, formatter = currency) {
        const number = Number(value) || 0;
        return `${number >= 0 ? '+' : '−'}${formatter(Math.abs(number))}`;
    }

    function localDate() {
        const today = new Date();
        return `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
    }

    function showNotification(message, type = 'success') {
        elements.toast.textContent = message;
        elements.toast.className = `toast ${type === 'error' ? 'error' : ''}`;
        window.clearTimeout(toastTimer);
        toastTimer = window.setTimeout(() => elements.toast.classList.add('hidden'), 5000);
    }

    async function api(url, options = {}) {
        let response;
        try {
            response = await fetch(url, options);
        } catch (error) {
            throw new Error(`Could not reach the Flask server: ${error.message}`);
        }
        let result;
        try {
            result = await response.json();
        } catch {
            throw new Error(`The server returned an unreadable response (${response.status}).`);
        }
        if (!response.ok || result.status === 'error') {
            throw new Error(result.message || `Request failed (${response.status}).`);
        }
        return result;
    }

    function navigateToPage(page) {
        setPage(page);
        if (page === 'market') {
            loadMarket().catch((error) => showNotification(error.message, 'error'));
        } else if (page === 'investors') {
            loadInvestors().catch((error) => showNotification(error.message, 'error'));
        } else if (page === 'investor-workspace') {
            loadInvestorWorkspace().catch((error) => showNotification(error.message, 'error'));
        } else if (page === 'watchlist') {
            loadWatchlist().catch((error) => showNotification(error.message, 'error'));
        } else if (page === 'securities') {
            loadWatchlist().catch((error) => showNotification(error.message, 'error'));
        } else if (page === 'security-detail' && state.securityDetailId) {
            loadSecurityDetail(state.securityDetailId).catch((error) => showNotification(error.message, 'error'));
        } else if (page === 'portfolio-detail' && state.portfolioDetailId) {
            loadPortfolioDetail(state.portfolioDetailId).catch((error) => showNotification(error.message, 'error'));
        } else if ([
            'portfolio-overview', 'portfolios', 'holdings', 'transactions', 'analytics', 'risk',
        ].includes(page)) {
            refreshData();
        }
    }

    function setPage(page, updateHash = true) {
        if (!pageCopy[page]) return;
        state.currentPage = page;
        const privatePages = new Set([
            'portfolio-overview', 'investor-workspace', 'portfolios', 'holdings',
            'transactions', 'watchlist', 'analytics', 'risk', 'portfolio-detail',
        ]);
        document.querySelectorAll('.page-view').forEach((view) => {
            view.classList.toggle('active', view.id === `page-${page}`);
            if (!privatePages.has(view.id.replace('page-', ''))) return;
            let gate = view.querySelector(':scope > .investor-required');
            if (!gate) {
                gate = document.createElement('article');
                gate.className = 'panel investor-required';
                gate.innerHTML = '<div class="empty-state"><strong>Select an investor to continue.</strong><p>Investment information is shown only after you choose an investor in the header.</p><button class="button button-primary" type="button" data-select-investor>Select investor</button></div>';
                view.prepend(gate);
            }
            const hasInvestor = Boolean(state.selectedInvestorId) && !state.investorContextLoading;
            gate.classList.toggle('hidden', hasInvestor);
            gate.querySelector('strong').textContent = state.investorContextLoading
                ? 'Loading selected investor…' : 'Select an investor to continue.';
            gate.querySelector('p').textContent = state.investorContextLoading
                ? 'Investment information will appear when the selected investor’s data is ready.'
                : 'Investment information is shown only after you choose an investor in the header.';
            gate.querySelector('button').classList.toggle('hidden', state.investorContextLoading);
            [...view.children].forEach((child) => {
                if (child !== gate) child.classList.toggle('hidden', !hasInvestor);
            });
        });
        document.querySelectorAll('.nav-link').forEach((link) => {
            const navPage = page === 'security-detail' ? 'securities'
                : page === 'portfolio-detail' ? 'portfolios'
                    : page === 'investor-workspace' ? 'investors' : page;
            const active = link.dataset.page === navPage;
            link.classList.toggle('active', active);
            if (active) link.setAttribute('aria-current', 'page');
            else link.removeAttribute('aria-current');
        });
        elements.pageTitle.textContent = pageCopy[page][0];
        elements.pageEyebrow.textContent = pageCopy[page][1];
        document.title = `EquityDesk — ${pageCopy[page][0]}`;
        elements.sidebar.classList.remove('open');
        if (updateHash && window.location.hash !== `#${page}`) {
            history.replaceState(null, '', `#${page}`);
        }
    }

    function appendOption(select, value, label) {
        const option = document.createElement('option');
        option.value = value;
        option.textContent = label;
        select.appendChild(option);
    }

    function populateInvestors() {
        const currentInvestor = elements.investorFilter.value;
        [elements.investorFilter, elements.formInvestor, elements.portfolioInvestor].forEach((select) => {
            const first = select.options[0];
            select.replaceChildren(first);
        });
        state.investors.forEach((investor) => {
            const label = `${investor.investor_name} (#${investor.investor_id})`;
            appendOption(elements.investorFilter, investor.investor_id, investor.investor_name);
            appendOption(elements.formInvestor, investor.investor_id, label);
            appendOption(elements.portfolioInvestor, investor.investor_id, label);
        });
        elements.investorFilter.value = state.investors.some((item) => String(item.investor_id) === currentInvestor)
            ? currentInvestor : state.selectedInvestorId;
    }

    function fillPortfolioSelect(select, portfolios, placeholder) {
        select.replaceChildren();
        appendOption(select, '', placeholder);
        portfolios.forEach((portfolio) => {
            appendOption(select, portfolio.portfolio_id, `${portfolio.portfolio_name} (#${portfolio.portfolio_id})`);
        });
    }

    function populateSecurities() {
        elements.formSecurity.replaceChildren();
        appendOption(elements.formSecurity, '', 'Choose security');
        state.securities.forEach((security) => {
            appendOption(
                elements.formSecurity,
                security.security_id,
                `${security.symbol} · ${security.security_name} (${currency(security.current_price)})`,
            );
        });
        const sectors = [...new Set(state.securities.map((item) => item.sector || 'Unclassified'))].sort();
        [elements.securitySector, elements.holdingsSector, elements.marketSector, elements.watchlistSector].forEach((select) => {
            const previous = select.value;
            select.replaceChildren();
            appendOption(select, '', 'All sectors');
            sectors.forEach((sector) => appendOption(select, sector, sector));
            if (sectors.includes(previous)) select.value = previous;
        });
        const selectedSecurity = elements.tradeSecurityFilter.value;
        elements.tradeSecurityFilter.replaceChildren();
        appendOption(elements.tradeSecurityFilter, '', 'All securities');
        state.securities.forEach((security) => {
            appendOption(elements.tradeSecurityFilter, security.security_id, `${security.symbol} · ${security.security_name}`);
        });
        elements.tradeSecurityFilter.value = state.securities.some((security) => String(security.security_id) === selectedSecurity)
            ? selectedSecurity : '';
    }

    async function checkHealth() {
        try {
            await api('/api/health');
            elements.backendStatus.textContent = 'Backend online';
            try {
                await api('/api/test-db');
                elements.databaseStatus.textContent = 'MySQL connected';
                elements.statusDot.className = 'status-dot online';
            } catch (error) {
                elements.databaseStatus.textContent = 'MySQL unavailable';
                elements.statusDot.className = 'status-dot offline';
                showNotification(error.message, 'error');
            }
        } catch {
            elements.backendStatus.textContent = 'Backend offline';
            elements.databaseStatus.textContent = 'Start Flask to connect';
            elements.statusDot.className = 'status-dot offline';
        }
    }

    function activeScope() {
        const params = new URLSearchParams();
        if (state.selectedInvestorId) params.set('investor_id', state.selectedInvestorId);
        if (state.selectedPortfolioId) params.set('portfolio_id', state.selectedPortfolioId);
        return params;
    }

    async function loadPortfolios() {
        if (!state.selectedInvestorId) {
            state.portfolios = [];
            fillPortfolioSelect(elements.portfolioFilter, [], 'Select investor first');
            fillPortfolioSelect(elements.tradePortfolioFilter, [], 'Select investor first');
            elements.portfolioFilter.disabled = true;
            renderPortfolios();
            return;
        }
        const params = new URLSearchParams();
        params.set('investor_id', state.selectedInvestorId);
        const result = await api(`/api/portfolios${params.size ? `?${params}` : ''}`);
        state.portfolios = result.data;
        const selectedPortfolio = String(state.selectedPortfolioId);
        fillPortfolioSelect(elements.portfolioFilter, state.portfolios, 'All portfolios');
        fillPortfolioSelect(elements.tradePortfolioFilter, state.portfolios, 'All portfolios');
        elements.portfolioFilter.disabled = false;
        if (state.portfolios.some((item) => String(item.portfolio_id) === selectedPortfolio)) {
            elements.portfolioFilter.value = selectedPortfolio;
        } else {
            state.selectedPortfolioId = '';
        }
        renderPortfolios();
        byId('metric-portfolios').textContent = state.portfolios.length.toLocaleString('en-IN');
    }

    async function loadMarket() {
        const params = new URLSearchParams();
        const search = elements.marketSearch.value.trim();
        const sector = elements.marketSector.value;
        const [sort, order] = elements.marketSort.value.split(':');
        if (search) params.set('search', search);
        if (sector) params.set('sector', sector);
        if (elements.marketMinPrice.value) params.set('min_price', elements.marketMinPrice.value);
        if (elements.marketMaxPrice.value) params.set('max_price', elements.marketMaxPrice.value);
        if (sort) params.set('sort', sort);
        if (order) params.set('order', order);
        const result = await api(`/api/market?${params}`);
        state.market = result;
        state.marketSecurities = result.securities;
        renderMarket();
    }

    async function loadInvestors() {
        const result = await api('/api/investors');
        state.investors = result.data;
        populateInvestors();
        renderInvestors();
    }

    async function loadInvestorWorkspace() {
        const investorId = state.selectedInvestorId;
        if (!investorId) return;
        const params = new URLSearchParams({ investor_id: investorId });
        const [investorsResult, portfoliosResult, holdingsResult, tradesResult, analyticsResult] = await Promise.all([
            api(`/api/investors?investor_id=${encodeURIComponent(investorId)}`),
            api(`/api/portfolios?${params}`),
            api(`/api/holdings?${params}`),
            api(`/api/trades?${params}&limit=1000`),
            api(`/api/analytics?${params}`),
        ]);
        state.selectedInvestor = investorsResult.data.find((item) => String(item.investor_id) === investorId) || null;
        state.investorHoldings = holdingsResult.data;
        state.investorTrades = tradesResult.data;
        renderInvestorWorkspace(portfoliosResult.data, holdingsResult.summary, analyticsResult);
    }

    async function loadWatchlist() {
        if (!state.selectedInvestorId) {
            state.watchlist = [];
            renderWatchlist();
            return;
        }
        const result = await api(`/api/watchlist?investor_id=${encodeURIComponent(state.selectedInvestorId)}`);
        state.watchlist = result.data;
        renderWatchlist();
    }

    async function loadHoldings() {
        if (!state.selectedInvestorId) {
            state.holdings = [];
            renderHoldings();
            return;
        }
        const params = activeScope();
        const result = await api(`/api/holdings${params.size ? `?${params}` : ''}`);
        state.holdings = result.data;
        renderHoldings(result.summary);
    }

    async function loadTrades() {
        if (!state.selectedInvestorId) {
            state.trades = [];
            renderTrades();
            return;
        }
        const params = activeScope();
        params.set('limit', state.currentPage === 'transactions' ? '1000' : '50');
        if (state.currentPage === 'transactions') {
            const type = elements.tradeTypeFilter.value;
            const portfolioId = elements.tradePortfolioFilter.value;
            const fromDate = elements.tradeFromDate.value;
            const toDate = elements.tradeToDate.value;
            const securityId = elements.tradeSecurityFilter.value;
            const search = elements.tradeSearch.value.trim();
            if (type) params.set('trade_type', type);
            if (portfolioId) params.set('portfolio_id', portfolioId);
            if (securityId) params.set('security_id', securityId);
            if (search) params.set('search', search);
            if (fromDate) params.set('from_date', fromDate);
            if (toDate) params.set('to_date', toDate);
        }
        const result = await api(`/api/trades?${params}`);
        state.trades = result.data;
        renderTrades();
        if (state.currentPage === 'transactions') renderMonthlySummary();
    }

    async function loadAnalytics() {
        if (!state.selectedInvestorId) {
            state.analytics = null;
            return;
        }
        const params = activeScope();
        state.analytics = await api(`/api/analytics${params.size ? `?${params}` : ''}`);
        renderAnalytics();
    }

    async function refreshData() {
        if (!state.selectedInvestorId) {
            state.portfolios = [];
            state.holdings = [];
            state.trades = [];
            state.analytics = null;
            renderPortfolios();
            renderHoldings();
            renderTrades();
            return;
        }
        const sequence = ++state.refreshSequence;
        const results = await Promise.allSettled([
            loadPortfolios(),
            loadHoldings(),
            loadTrades(),
            loadAnalytics(),
        ]);
        if (sequence !== state.refreshSequence) return;
        const failure = results.find((result) => result.status === 'rejected');
        if (failure) {
            showNotification(failure.reason.message, 'error');
            if (failure.reason.message.includes('Flask server')) {
                elements.statusDot.className = 'status-dot offline';
                elements.databaseStatus.textContent = 'Connection failed';
            }
        }
        renderDashboard();
        if (state.currentPage === 'investor-workspace') {
            await loadInvestorWorkspace().catch((error) => showNotification(error.message, 'error'));
        }
    }

    function symbolCell(symbol, name) {
        const initials = escapeHtml(String(symbol || '??').slice(0, 3));
        return `<div class="symbol-cell"><span class="symbol-badge">${initials}</span><span class="symbol-copy"><strong>${escapeHtml(symbol)}</strong><small>${escapeHtml(name)}</small></span></div>`;
    }

    function renderDashboard() {
        const analytics = state.analytics;
        if (!analytics) return;
        const summary = analytics.summary;
        byId('metric-current').textContent = currency(summary.current_value);
        byId('metric-invested').textContent = currency(summary.total_invested);
        byId('metric-pnl').textContent = signed(summary.total_pnl);
        byId('metric-return').textContent = `${summary.pnl_percentage >= 0 ? '+' : ''}${Number(summary.pnl_percentage).toFixed(2)}%`;
        byId('metric-stocks').textContent = summary.stocks_held.toLocaleString('en-IN');
        byId('metric-pnl').closest('.metric-card').classList.toggle('positive', summary.total_pnl >= 0);
        byId('metric-pnl').closest('.metric-card').classList.toggle('negative', summary.total_pnl < 0);
        byId('metric-return').closest('.metric-card').classList.toggle('positive', summary.pnl_percentage >= 0);
        byId('metric-return').closest('.metric-card').classList.toggle('negative', summary.pnl_percentage < 0);
        const scopeName = state.selectedPortfolioId
            ? state.portfolios.find((item) => String(item.portfolio_id) === String(state.selectedPortfolioId))?.portfolio_name
            : null;
        byId('metric-current-note').textContent = scopeName ? `${scopeName} · database prices` : 'At prices in your database';
        byId('metric-pnl-note').textContent = summary.total_pnl >= 0 ? 'Unrealized gain on open positions' : 'Unrealized loss on open positions';
        drawPortfolioChart(byId('performance-chart'), analytics.portfolio_performance || []);
        drawAllocationChart(analytics.sector_allocation || [], summary.current_value);
        renderBestPerformers(analytics.top_performers || [], byId('best-performers'), 4);
        renderRisk(analytics.risk || {});
    }

    function renderMarketList(container, rows, type) {
        container.innerHTML = rows.map((row) => `
            <div class="market-list-row">
                <span class="market-list-name"><strong>${escapeHtml(row.symbol)}</strong><small>${escapeHtml(row.name)} · ${escapeHtml(row.sector)}</small></span>
                <span class="market-list-metric"><strong>${demoCurrency(row.price, row.currency)}</strong><small class="${row.change >= 0 ? 'positive-text' : 'negative-text'}">${row.change >= 0 ? '+' : ''}${Number(row.change).toFixed(2)}%</small></span>
                ${row.volume ? `<span class="demo-volume">${escapeHtml(row.volume)}<small>${type === 'shockers' ? 'vs weekly avg.' : 'demo volume'}</small></span>` : ''}
            </div>`).join('');
    }

    function demoCurrency(value, currencyCode = 'INR') {
        return currencyCode === 'USD'
            ? `$${Number(value).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
            : currency(value);
    }

    function renderSyntheticMarket() {
        byId('market-indices').innerHTML = demoMarket.indices.map((index) => `
            <article class="index-card demo-index-card">
                <div class="index-card-top"><strong>${escapeHtml(index.name)}</strong><span>DEMO INDEX</span></div>
                <strong class="index-value">${escapeHtml(index.value)}</strong>
                <small class="${index.change >= 0 ? 'positive-text' : 'negative-text'}">${index.change >= 0 ? '+' : ''}${Number(index.change).toFixed(2)} · ${index.change >= 0 ? '+' : ''}${Number(index.percent).toFixed(2)}%</small>
            </article>
        `).join('');
        renderMarketList(byId('market-gainers'), demoMarket.gainers, 'gainers');
        renderMarketList(byId('market-losers'), demoMarket.losers, 'losers');
        renderMarketList(byId('market-most-bought'), demoMarket.traded, 'traded');
        renderMarketList(byId('market-intraday'), demoMarket.intraday, 'intraday');
        renderMarketList(byId('market-mtf'), demoMarket.mtf, 'mtf');
        renderMarketList(byId('market-shockers'), demoMarket.shockers, 'shockers');
        renderMarketList(byId('market-etfs'), demoMarket.etfs, 'etfs');
        renderMarketList(byId('market-us'), demoMarket.global, 'global');
        byId('market-sector-performance').innerHTML = demoMarket.sectors.map((sector) => `
            <div class="sector-return-card"><span>${escapeHtml(sector.name)}</span><strong class="${sector.change >= 0 ? 'positive-text' : 'negative-text'}">${sector.change >= 0 ? '+' : ''}${sector.change.toFixed(2)}%</strong></div>
        `).join('');
        byId('market-news').innerHTML = demoMarket.news.map((item) => `
            <article class="market-news-item"><div><strong>${escapeHtml(item.symbol)}</strong><small>${escapeHtml(item.time)}</small></div><p>${escapeHtml(item.headline)}</p></article>
        `).join('');
    }

    function renderSecurityCards(securities, container, limit = Infinity) {
        const rows = securities.slice(0, limit);
        container.innerHTML = rows.length ? rows.map((security) => {
            const watched = state.watchlist.some((item) => Number(item.security_id) === Number(security.security_id));
            return `<article class="stock-card">
                <div class="stock-card-top"><button class="stock-card-identity" data-action="view-security" data-id="${Number(security.security_id)}"><strong>${escapeHtml(security.symbol)}</strong><span>${escapeHtml(security.security_name)}</span></button><span class="pill">${escapeHtml(security.sector || 'Unclassified')}</span></div>
                <div class="stock-card-price"><small>Stored database price</small><strong>${currency(security.current_price)}</strong><small class="muted-copy">Historical movement unavailable</small></div>
                <div class="stock-card-actions"><button class="row-action" data-action="toggle-watchlist" data-id="${Number(security.security_id)}">${watched ? '★ Remove from watchlist' : '☆ Add to watchlist'}</button><button class="text-button" data-action="view-security" data-id="${Number(security.security_id)}">View details →</button></div>
            </article>`;
        }).join('') : '<div class="empty-state">No securities match these filters.</div>';
    }

    function renderMarket() {
        if (!state.market) return;
        renderSyntheticMarket();
        renderSecurityCards(state.market.securities || [], byId('market-security-grid'), 6);
    }

    function renderInvestors() {
        const search = elements.investorSearch.value.trim().toLocaleLowerCase();
        const investors = state.investors.filter((investor) =>
            `${investor.investor_name} ${investor.investor_id}`.toLocaleLowerCase().includes(search));
        byId('investor-count').textContent = `${investors.length} ${investors.length === 1 ? 'investor' : 'investors'}`;
        byId('investors-grid').innerHTML = investors.length ? investors.map((investor) => {
            const selected = String(investor.investor_id) === String(state.selectedInvestorId);
            const portfolioCount = investor.portfolio_count !== undefined
                ? Number(investor.portfolio_count)
                : selected ? state.portfolios.length : null;
            const initials = investor.investor_name.split(/\s+/).slice(0, 2).map((part) => part[0]).join('').toUpperCase();
            return `<article class="investor-card${selected ? ' selected' : ''}">
                <div class="investor-card-top"><span class="investor-avatar">${escapeHtml(initials)}</span><span class="pill">ID ${Number(investor.investor_id)}</span></div>
                <h3>${escapeHtml(investor.investor_name)}</h3>
                <p>${portfolioCount === null ? 'Portfolio count available after selection' : `${portfolioCount} ${portfolioCount === 1 ? 'portfolio' : 'portfolios'}`}</p>
                <button class="button ${selected ? 'button-secondary' : 'button-primary'} button-full" data-action="view-investor" data-id="${Number(investor.investor_id)}">${selected ? 'Selected investor' : 'Select investor'}</button>
            </article>`;
        }).join('') : '<div class="empty-state">No investors match your search.</div>';
    }

    function renderInvestorWorkspace(portfolios, summary, analytics) {
        const investor = state.selectedInvestor;
        if (!investor) {
            showNotification('Investor record was not found.', 'error');
            navigateToPage('investors');
            return;
        }
        byId('investor-workspace-name').textContent = investor.investor_name;
        byId('investor-workspace-contact').textContent = 'Only this investor’s portfolios, holdings and transactions are shown.';
        byId('investor-metric-invested').textContent = currency(summary.total_invested);
        byId('investor-metric-current').textContent = currency(summary.current_value);
        byId('investor-metric-pnl').textContent = signed(summary.total_pnl);
        byId('investor-metric-pnl').classList.toggle('positive-text', summary.total_pnl >= 0);
        byId('investor-metric-pnl').classList.toggle('negative-text', summary.total_pnl < 0);
        byId('investor-metric-return').textContent = `${Number(summary.pnl_percentage) >= 0 ? '+' : ''}${Number(summary.pnl_percentage).toFixed(2)}% unrealized return`;
        byId('investor-metric-portfolios').textContent = portfolios.length.toLocaleString('en-IN');
        byId('investor-portfolio-list').innerHTML = portfolios.length ? portfolios.map((portfolio) => {
            const invested = Number(portfolio.total_invested);
            const pnl = Number(portfolio.total_pnl);
            const returnValue = portfolio.return_percentage === null ? null : Number(portfolio.return_percentage);
            return `<button class="investor-portfolio-row" data-action="view-portfolio" data-id="${Number(portfolio.portfolio_id)}">
                <span><strong>${escapeHtml(portfolio.portfolio_name)}</strong><small>${escapeHtml(portfolio.created_date)} · ${currency(invested)} invested</small></span>
                <span><strong>${currency(portfolio.current_value)}</strong><small class="${pnl >= 0 ? 'positive-text' : 'negative-text'}">${signed(pnl)} · ${returnValue === null ? '—' : `${returnValue >= 0 ? '+' : ''}${returnValue.toFixed(2)}%`}</small></span></button>`;
        }).join('') : '<div class="empty-state">This investor has no portfolios yet.</div>';
        byId('investor-holdings-table').innerHTML = state.investorHoldings.length ? state.investorHoldings.map((holding) => `
            <tr><td>${symbolCell(holding.symbol, holding.security_name)}</td><td>${escapeHtml(holding.portfolio_name)}</td>
                <td>${escapeHtml(holding.sector)}</td><td class="align-right">${Number(holding.quantity).toLocaleString('en-IN')}</td>
                <td class="align-right">${currency(holding.invested_value)}</td><td class="align-right">${currency(holding.current_value)}</td>
                <td class="align-right ${Number(holding.pnl) >= 0 ? 'positive-text' : 'negative-text'}">${signed(holding.pnl)}</td></tr>
        `).join('') : '<tr><td colspan="7" class="empty-cell">No open holdings for this investor.</td></tr>';
        byId('investor-trades-table').innerHTML = state.investorTrades.length ? state.investorTrades.map((trade) => `
            <tr><td>${escapeHtml(trade.trade_date)}</td><td>${escapeHtml(trade.portfolio_name)}</td>
                <td>${symbolCell(trade.symbol, trade.security_name)}</td><td><span class="trade-tag ${trade.trade_type === 'BUY' ? 'buy' : 'sell'}">${escapeHtml(trade.trade_type)}</span></td>
                <td class="align-right">${Number(trade.quantity).toLocaleString('en-IN')}</td><td class="align-right">${currency(trade.total_trade_amount)}</td></tr>
        `).join('') : '<tr><td colspan="6" class="empty-cell">No transactions recorded for this investor.</td></tr>';
        renderBars(byId('investor-sector-allocation'), analytics.sector_allocation || []);
        renderBestPerformers(analytics.top_performers || [], byId('investor-performers'), 5);
    }

    function renderMonthlySummary() {
        const months = new Map();
        state.trades.forEach((trade) => {
            if (Number(trade.is_voided || 0)) return;
            const month = trade.trade_date.slice(0, 7);
            if (!months.has(month)) months.set(month, { month, buy_count: 0, sell_count: 0, buy_value: 0, sell_value: 0 });
            const summary = months.get(month);
            const type = trade.trade_type.toLowerCase();
            summary[`${type}_count`] += 1;
            summary[`${type}_value`] += Number(trade.total_trade_amount);
        });
        const summaries = [...months.values()].sort((a, b) => b.month.localeCompare(a.month)).slice(0, 6);
        byId('monthly-trade-summary').innerHTML = summaries.length ? summaries.map((month) => `
            <div class="month-summary"><strong>${escapeHtml(month.month)}</strong><span class="positive-text">BUY ${month.buy_count} · ${currency(month.buy_value, true)}</span><span class="negative-text">SELL ${month.sell_count} · ${currency(month.sell_value, true)}</span></div>
        `).join('') : '<div class="empty-state">No transaction activity for this selection.</div>';
    }

    function renderMonthlyActivity() {
        const rows = state.analytics?.monthly_activity || [];
        const max = Math.max(1, ...rows.map((row) => Number(row.buy_count) + Number(row.sell_count)));
        byId('monthly-activity-chart').innerHTML = rows.length ? rows.slice(-12).map((row) => {
            const buy = Number(row.buy_count);
            const sell = Number(row.sell_count);
            const total = buy + sell;
            return `<div class="month-bar"><div class="month-bar-stack" title="${buy} BUY · ${sell} SELL">
                    <span class="month-buy-bar" style="height:${buy / max * 100}%"></span><span class="month-sell-bar" style="height:${sell / max * 100}%"></span>
                </div><strong>${escapeHtml(row.month.slice(5))}</strong><small>${total} trades</small></div>`;
        }).join('') : '<div class="empty-state">No transaction history is available for this view.</div>';
    }

    function renderHoldings(summary) {
        const search = elements.holdingsSearch.value.trim().toLocaleLowerCase();
        const sector = elements.holdingsSector.value;
        const [sortKey, sortOrder] = elements.holdingsSort.value.split(':');
        const grouped = elements.holdingsGroupToggle.checked;
        let rows = state.holdings.filter((item) => {
            const matchesSector = !sector || (item.sector || 'Unclassified') === sector;
            const matchesSearch = !search || `${item.symbol} ${item.security_name} ${item.portfolio_name}`
                .toLocaleLowerCase().includes(search);
            return matchesSector && matchesSearch;
        });
        if (grouped) {
            const groups = new Map();
            rows.forEach((item) => {
                const key = Number(item.security_id);
                const current = groups.get(key);
                if (!current) {
                    groups.set(key, {
                        ...item,
                        portfolio_count: 1,
                        quantity: Number(item.quantity),
                        invested_value: Number(item.invested_value),
                        current_value: Number(item.current_value),
                        realized_pnl: Number(item.realized_pnl || 0),
                        unrealized_pnl: Number(item.unrealized_pnl || item.pnl || 0),
                        pnl: Number(item.pnl || item.unrealized_pnl || 0),
                    });
                    return;
                }
                current.quantity += Number(item.quantity);
                current.invested_value += Number(item.invested_value);
                current.current_value += Number(item.current_value);
                current.realized_pnl += Number(item.realized_pnl || 0);
                current.unrealized_pnl += Number(item.unrealized_pnl || item.pnl || 0);
                current.pnl += Number(item.pnl || item.unrealized_pnl || 0);
                current.portfolio_count += 1;
            });
            rows = [...groups.values()].map((item) => ({
                ...item,
                average_buy_price: item.quantity ? item.invested_value / item.quantity : 0,
                pnl_percentage: item.invested_value ? item.pnl / item.invested_value * 100 : 0,
                portfolio_name: `${item.portfolio_count} ${item.portfolio_count === 1 ? 'portfolio' : 'portfolios'}`,
            }));
        }
        rows.sort((left, right) => {
            const a = Number(left[sortKey]) || 0;
            const b = Number(right[sortKey]) || 0;
            const comparison = sortKey === 'symbol'
                ? String(left.symbol).localeCompare(String(right.symbol))
                : a - b;
            return sortOrder === 'desc' ? -comparison : comparison;
        });
        const positionCount = state.holdings.length;
        byId('holdings-count').textContent = grouped
            ? `${rows.length} securities · ${positionCount} positions`
            : `${positionCount} ${positionCount === 1 ? 'position' : 'positions'}`;
        if (!rows.length) {
            byId('holdings-grid').innerHTML = '<div class="empty-state holdings-empty">No positions match this view. Record a BUY transaction to add a holding.</div>';
            return;
        }
        byId('holdings-grid').innerHTML = rows.map((item) => {
            const unrealizedPnl = Number(item.unrealized_pnl || item.pnl || 0);
            const pnlClass = unrealizedPnl >= 0 ? 'positive-text' : 'negative-text';
            const realizedPnl = Number(item.realized_pnl || 0);
            const returnPercentage = Number(item.pnl_percentage) || 0;
            return `<article class="holding-card">
                <div class="holding-card-head"><div class="holding-symbol"><span class="symbol-badge">${escapeHtml(String(item.symbol || '??').slice(0, 3))}</span><div><strong>${escapeHtml(item.symbol)}</strong><small>${escapeHtml(item.security_name)}</small></div></div><strong class="holding-pnl ${pnlClass}">${signed(unrealizedPnl)}</strong></div>
                <div class="holding-context"><span>${escapeHtml(item.portfolio_name)}</span><span class="pill">${escapeHtml(item.sector || 'Unclassified')}</span></div>
                <div class="holding-price-strip"><span>Quantity <strong>${Number(item.quantity).toLocaleString('en-IN')}</strong></span><span>Return <strong class="${pnlClass}">${returnPercentage >= 0 ? '+' : ''}${returnPercentage.toFixed(2)}%</strong></span></div>
                <div class="holding-values">
                    <span><small>Average buy</small><strong>${currency(item.average_buy_price)}</strong></span>
                    <span><small>Stored price</small><strong>${currency(item.current_price)}</strong></span>
                    <span><small>Invested</small><strong>${currency(item.invested_value, true)}</strong></span>
                    <span><small>Current value</small><strong>${currency(item.current_value, true)}</strong></span>
                </div>
                <div class="holding-card-foot"><span>Unrealized <strong class="${pnlClass}">${signed(unrealizedPnl)}</strong></span><span>Realized <strong class="${realizedPnl >= 0 ? 'positive-text' : 'negative-text'}">${signed(realizedPnl)}</strong></span></div>
            </article>`;
        }).join('');
        if (summary) {
            byId('metric-invested').textContent = currency(summary.total_invested);
        }
    }

    function renderTrades() {
        const status = elements.tradeStatusFilter.value;
        const trades = state.trades.filter((trade) =>
            !status || (status === 'voided') === (Number(trade.is_voided || 0) === 1));
        byId('trades-count').textContent = `${trades.length} ${trades.length === 1 ? 'record' : 'records'}`;
        const recent = state.trades.slice(0, 5);
        byId('recent-trades').innerHTML = recent.length ? recent.map((trade) => `
            <tr><td>${symbolCell(trade.symbol, trade.security_name)}</td>
            <td><span class="trade-tag ${trade.trade_type === 'BUY' ? 'buy' : 'sell'}">${escapeHtml(trade.trade_type)}</span></td>
            <td>${escapeHtml(trade.trade_date)}</td><td class="align-right">${currency(trade.total_trade_amount)}</td></tr>
        `).join('') : '<tr><td colspan="4" class="empty-cell">No transactions recorded yet.</td></tr>';
        byId('trades-table').innerHTML = trades.length ? trades.map((trade) => {
            const voided = Number(trade.is_voided || 0) === 1;
            const statusText = voided ? 'Voided' : 'Active';
            const statusClass = voided ? 'negative-text' : 'positive-text';
            return `<tr>
                <td>${Number(trade.trade_id)}</td><td>${escapeHtml(trade.trade_date)}</td><td>${symbolCell(trade.symbol, trade.security_name)}</td>
                <td>${escapeHtml(trade.portfolio_name)}</td><td><span class="trade-tag ${trade.trade_type === 'BUY' ? 'buy' : 'sell'}">${escapeHtml(trade.trade_type)}</span></td>
                <td class="align-right">${Number(trade.quantity).toLocaleString('en-IN')}</td><td class="align-right">${currency(trade.trade_price)}</td>
                <td class="align-right">${currency(trade.total_trade_amount)}</td><td class="${statusClass}">${statusText}</td>
                <td>${voided ? `<span>${escapeHtml(trade.void_reason || 'Voided transaction')}</span><br><small>${escapeHtml(trade.voided_by || 'Unknown user')} · ${escapeHtml(trade.voided_at || 'Time unavailable')}</small>` : '—'}</td>
                <td>${voided ? '<span class="pill">Closed</span>' : `<button class="row-action danger" data-action="void-trade" data-id="${Number(trade.trade_id)}">Void</button>`}</td>
            </tr>`;
        }).join('') : '<tr><td colspan="11" class="empty-cell">No transactions match these filters.</td></tr>';
    }

    async function openVoidTradeModal(tradeId) {
        elements.voidTradeId.value = String(tradeId);
        elements.voidTradeReason.value = '';
        elements.voidTradeModal.showModal();
    }

    async function voidTrade(tradeId, reason) {
        const result = await api(`/api/trades/${encodeURIComponent(tradeId)}/void`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                investor_id: Number(state.selectedInvestorId),
                reason,
                performed_by: 'equitydesk-user',
            }),
        });
        showNotification(result.message || 'Transaction voided successfully.', 'success');
        await refreshData();
        return result;
    }

    function renderPortfolios() {
        const grid = byId('portfolio-grid');
        const search = elements.portfolioSearch.value.trim().toLocaleLowerCase();
        const [sortKey, sortOrder] = elements.portfolioSort.value.split(':');
        const portfolios = state.portfolios.filter((portfolio) =>
            `${portfolio.portfolio_name} ${portfolio.investor_name}`.toLocaleLowerCase().includes(search))
            .sort((left, right) => {
                const a = left[sortKey];
                const b = right[sortKey];
                const comparison = typeof a === 'number' || typeof b === 'number'
                    ? Number(a || 0) - Number(b || 0)
                    : String(a || '').localeCompare(String(b || ''));
                return sortOrder === 'asc' ? comparison : -comparison;
            });
        grid.innerHTML = portfolioCardsMarkup(portfolios, false);
        byId('overview-portfolio-grid').innerHTML = portfolioCardsMarkup(state.portfolios, true);
    }

    function portfolioCardsMarkup(portfolios, overview) {
        if (!portfolios.length) {
            return `<div class="panel empty-state">${overview ? 'No portfolios yet. Create one to organize your investments.' : 'No portfolios found. Create one to start organizing your investments.'}</div>`;
        }
        return portfolios.map((portfolio) => {
            const pnl = Number(portfolio.total_pnl);
            const returnPct = portfolio.return_percentage === null ? null : Number(portfolio.return_percentage);
            const sectors = portfolio.sector_allocation || [];
            const currentValue = Number(portfolio.current_value);
            const positionCount = Number(portfolio.holding_count || 0);
            return `<article class="portfolio-card portfolio-card-clickable" data-action="view-portfolio" data-id="${Number(portfolio.portfolio_id)}" role="group" tabindex="0" aria-label="Portfolio ${escapeHtml(portfolio.portfolio_name)}. Activate to view details.">
                <div class="portfolio-card-top"><div><h3>${escapeHtml(portfolio.portfolio_name)}</h3><div class="portfolio-owner">${escapeHtml(portfolio.investor_name)} · Since ${escapeHtml(portfolio.created_date)}</div></div><span class="pill">#${Number(portfolio.portfolio_id)}</span></div>
                <div class="portfolio-card-value"><div><small>Current value</small><strong>${currency(portfolio.current_value)}</strong></div><div><small>Invested</small><strong>${currency(portfolio.total_invested)}</strong></div></div>
                <div class="portfolio-sector-list">${sectors.length ? sectors.slice(0, 3).map((sector) => `<span><i></i>${escapeHtml(sector.sector)}<b>${currentValue ? (Number(sector.current_value) / currentValue * 100).toFixed(0) : '0'}%</b></span>`).join('') : '<small>No open holdings in this portfolio.</small>'}</div>
                <small class="portfolio-holding-count">${positionCount} open ${positionCount === 1 ? 'position' : 'positions'}</small>
                <div class="portfolio-pnl-grid"><span>Realized <b class="${Number(portfolio.realized_pnl) >= 0 ? 'positive-text' : 'negative-text'}">${signed(portfolio.realized_pnl)}</b></span><span>Unrealized <b class="${Number(portfolio.unrealized_pnl) >= 0 ? 'positive-text' : 'negative-text'}">${signed(portfolio.unrealized_pnl)}</b></span></div>
                <div class="portfolio-card-bottom"><span class="portfolio-return ${pnl >= 0 ? 'positive-text' : 'negative-text'}">${signed(pnl)} total · ${returnPct === null ? '— return' : `${returnPct >= 0 ? '+' : ''}${returnPct.toFixed(2)}%`}</span>
                    <div class="portfolio-actions">${positionCount === 0 ? `<button class="row-action" data-action="record-portfolio-trade" data-open-trade data-portfolio-id="${Number(portfolio.portfolio_id)}" data-investor-id="${Number(portfolio.investor_id)}">Record first trade</button>` : ''}
                    ${overview ? '' : `<button class="row-action" data-action="edit-portfolio" data-id="${Number(portfolio.portfolio_id)}">Edit</button><button class="row-action danger" data-action="delete-portfolio" data-id="${Number(portfolio.portfolio_id)}" aria-label="Delete ${escapeHtml(portfolio.portfolio_name)}">Delete</button>`}</div>
                </div>
            </article>`;
        }).join('');
    }

    function renderSecurities() {
        const search = elements.securitySearch.value.trim().toLocaleLowerCase();
        const sector = elements.securitySector.value;
        const minPrice = elements.securityMinPrice.value === '' ? null : Number(elements.securityMinPrice.value);
        const maxPrice = elements.securityMaxPrice.value === '' ? null : Number(elements.securityMaxPrice.value);
        const [sortKey, sortOrder] = elements.securitySort.value.split(':');
        const securities = state.securities.filter((security) => {
            const matchesSector = !sector || (security.sector || 'Unclassified') === sector;
            const matchesSearch = !search || `${security.symbol} ${security.security_name}`.toLocaleLowerCase().includes(search);
            const price = Number(security.current_price);
            return matchesSector && matchesSearch && (minPrice === null || price >= minPrice) && (maxPrice === null || price <= maxPrice);
        }).sort((left, right) => {
            const a = sortKey === 'price' ? Number(left.current_price) : String(left[sortKey === 'company' ? 'security_name' : sortKey === 'sector' ? 'sector' : 'symbol'] || '');
            const b = sortKey === 'price' ? Number(right.current_price) : String(right[sortKey === 'company' ? 'security_name' : sortKey === 'sector' ? 'sector' : 'symbol'] || '');
            const comparison = typeof a === 'number' ? a - b : a.localeCompare(b);
            return sortOrder === 'desc' ? -comparison : comparison;
        });
        byId('security-count').textContent = `${securities.length} ${securities.length === 1 ? 'security' : 'securities'}`;
        renderSecurityCards(securities, byId('securities-grid'));
    }

    function renderWatchlist() {
        const body = byId('watchlist-table');
        if (!state.selectedInvestorId) {
            body.innerHTML = '<tr><td colspan="6" class="empty-cell">Select an investor in the header to view their watchlist.</td></tr>';
            return;
        }
        const search = elements.watchlistSearch.value.trim().toLocaleLowerCase();
        const sector = elements.watchlistSector.value;
        const rows = state.watchlist.filter((security) =>
            `${security.symbol} ${security.security_name}`.toLocaleLowerCase().includes(search) &&
            (!sector || (security.sector || 'Unclassified') === sector));
        body.innerHTML = rows.length ? rows.map((security) => `
            <tr><td>${symbolCell(security.symbol, security.security_name)}</td><td><span class="pill">${escapeHtml(security.sector || 'Unclassified')}</span></td>
                <td>${currency(security.current_price)}</td><td><div class="target-entry"><input type="number" min="0.01" step="0.01" aria-label="Target price for ${escapeHtml(security.symbol)}" data-target-value="${Number(security.security_id)}" value="${security.target_price ?? ''}" placeholder="Optional"><button class="row-action" data-action="save-target" data-id="${Number(security.security_id)}">Save</button></div></td>
                <td class="${Number(security.target_reached) ? 'positive-text' : 'muted-copy'}">${Number(security.target_reached) ? 'Target reached' : security.target_price ? 'Watching target' : 'No alert set'}</td>
                <td class="align-right"><button class="row-action danger" data-action="toggle-watchlist" data-id="${Number(security.security_id)}">Remove</button></td></tr>
        `).join('') : state.watchlist.length
            ? '<tr><td colspan="6" class="empty-cell">No securities match these watchlist filters.</td></tr>'
            : '<tr><td colspan="6" class="empty-cell">This investor’s watchlist is empty. <button class="text-button" data-navigate="securities">Browse securities</button> to add one.</td></tr>';
    }

    async function toggleWatchlist(id) {
        if (!state.selectedInvestorId) {
            showNotification('Select an investor in the header before adding securities to a watchlist.', 'error');
            elements.investorFilter.focus();
            return;
        }
        try {
            await loadWatchlist();
            const isWatched = state.watchlist.some((item) => Number(item.security_id) === id);
            const options = isWatched ? {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ investor_id: Number(state.selectedInvestorId), security_id: id }),
            } : {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ investor_id: Number(state.selectedInvestorId), security_id: id }),
            };
            const result = await api('/api/watchlist', options);
            showNotification(result.message);
            await loadWatchlist();
            renderSecurities();
        } catch (error) {
            setTradeFormError(error.message);
            showNotification(error.message, 'error');
        }
    }

    async function saveTargetPrice(id) {
        if (!state.selectedInvestorId) {
            showNotification('Select an investor to update their watchlist.', 'error');
            return;
        }
        const input = document.querySelector(`[data-target-value="${id}"]`);
        const target = input.value.trim();
        if (target && (!Number.isFinite(Number(target)) || Number(target) <= 0)) {
            showNotification('Target price must be greater than zero.', 'error');
            input.focus();
            return;
        }
        try {
            const result = await api('/api/watchlist', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    investor_id: Number(state.selectedInvestorId),
                    security_id: id,
                    target_price: target || null,
                }),
            });
            showNotification(result.message);
            await loadWatchlist();
        } catch (error) {
            showNotification(error.message, 'error');
        }
    }

    function exportCSV(filename, headers, rows) {
        const escapeCell = (value) => `"${String(value ?? '').replace(/"/g, '""')}"`;
        const contents = [headers, ...rows].map((row) => row.map(escapeCell).join(',')).join('\r\n');
        const blob = new Blob(['\uFEFF', contents], { type: 'text/csv;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const anchor = document.createElement('a');
        anchor.href = url;
        anchor.download = filename;
        document.body.appendChild(anchor);
        anchor.click();
        anchor.remove();
        URL.revokeObjectURL(url);
    }

    function svgNode(name, attributes = {}, text = '') {
        const node = document.createElementNS('http://www.w3.org/2000/svg', name);
        Object.entries(attributes).forEach(([key, value]) => node.setAttribute(key, value));
        if (text) node.textContent = text;
        return node;
    }

    function drawPortfolioChart(svg, rows) {
        const width = 760;
        const height = 220;
        const left = 61;
        const right = 12;
        const top = 14;
        const bottom = 35;
        const plotHeight = height - top - bottom;
        const plotWidth = width - left - right;
        svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
        svg.replaceChildren();
        const validRows = rows.filter((row) => Number(row.current_value) || Number(row.invested));
        if (!validRows.length) {
            svg.appendChild(svgNode('text', { x: width / 2, y: height / 2, 'text-anchor': 'middle', class: 'chart-empty' }, 'No current positions to compare'));
            return;
        }
        const maxValue = Math.max(1, ...validRows.flatMap((row) => [Number(row.invested), Number(row.current_value)]));
        for (let index = 0; index <= 3; index += 1) {
            const y = top + (plotHeight * index / 3);
            svg.appendChild(svgNode('line', { x1: left, y1: y, x2: width - right, y2: y, class: 'grid-line' }));
            const value = maxValue * (1 - index / 3);
            svg.appendChild(svgNode('text', { x: left - 8, y: y + 3, 'text-anchor': 'end', class: 'axis-label' }, currency(value, true)));
        }
        const slot = plotWidth / validRows.length;
        const barWidth = Math.min(25, Math.max(9, slot * .24));
        validRows.forEach((row, index) => {
            const center = left + slot * (index + .5);
            const invested = Number(row.invested) || 0;
            const current = Number(row.current_value) || 0;
            const investedHeight = invested / maxValue * plotHeight;
            const currentHeight = current / maxValue * plotHeight;
            const investedRect = svgNode('rect', {
                x: center - barWidth - 3, y: top + plotHeight - investedHeight, width: barWidth, height: investedHeight,
                rx: 3, class: 'bar-invested',
            });
            investedRect.appendChild(svgNode('title', {}, `Invested: ${currency(invested)}`));
            svg.appendChild(investedRect);
            const currentRect = svgNode('rect', {
                x: center + 3, y: top + plotHeight - currentHeight, width: barWidth, height: currentHeight,
                rx: 3, class: 'bar-current',
            });
            currentRect.appendChild(svgNode('title', {}, `Current value: ${currency(current)}`));
            svg.appendChild(currentRect);
            const label = String(row.portfolio_name || 'Portfolio');
            const shortLabel = label.length > 5 ? `${label.slice(0, 4)}…` : label;
            const axisLabel = svgNode('text', {
                x: center, y: height - 11, 'text-anchor': 'middle', class: 'axis-label',
            }, shortLabel);
            axisLabel.appendChild(svgNode('title', {}, label));
            svg.appendChild(axisLabel);
        });
    }

    function drawHistoryChart(svg, rows, valueKey, dateKey) {
        const width = 760;
        const height = 220;
        const left = 64;
        const right = 18;
        const top = 15;
        const bottom = 34;
        const plotWidth = width - left - right;
        const plotHeight = height - top - bottom;
        const validRows = rows.filter((row) => Number.isFinite(Number(row[valueKey])))
            .map((row) => ({ date: String(row[dateKey]), value: Number(row[valueKey]) }));
        svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
        svg.replaceChildren();
        if (validRows.length < 2) {
            svg.appendChild(svgNode('text', { x: width / 2, y: height / 2, 'text-anchor': 'middle', class: 'chart-empty' }, 'Not enough historical data'));
            return;
        }
        const values = validRows.map((row) => row.value);
        const minimum = Math.min(...values);
        const maximum = Math.max(...values);
        const span = Math.max(1, maximum - minimum);
        const minAxis = Math.max(0, minimum - span * .1);
        const maxAxis = maximum + span * .1 || 1;
        for (let index = 0; index <= 3; index += 1) {
            const y = top + plotHeight * index / 3;
            const value = maxAxis - (maxAxis - minAxis) * index / 3;
            svg.appendChild(svgNode('line', { x1: left, y1: y, x2: width - right, y2: y, class: 'grid-line' }));
            svg.appendChild(svgNode('text', { x: left - 8, y: y + 3, 'text-anchor': 'end', class: 'axis-label' }, currency(value, true)));
        }
        const coordinates = validRows.map((row, index) => ({
            ...row,
            x: left + (plotWidth * index / (validRows.length - 1)),
            y: top + plotHeight - ((row.value - minAxis) / (maxAxis - minAxis)) * plotHeight,
        }));
        svg.appendChild(svgNode('polyline', {
            points: coordinates.map((point) => `${point.x},${point.y}`).join(' '),
            class: 'history-line',
        }));
        coordinates.forEach((point, index) => {
            const circle = svgNode('circle', { cx: point.x, cy: point.y, r: 3, class: 'history-point' });
            circle.appendChild(svgNode('title', {}, `${point.date}: ${currency(point.value)}`));
            svg.appendChild(circle);
            if (index === 0 || index === coordinates.length - 1 || index === Math.floor(coordinates.length / 2)) {
                svg.appendChild(svgNode('text', {
                    x: point.x,
                    y: height - 11,
                    'text-anchor': index === 0 ? 'start' : index === coordinates.length - 1 ? 'end' : 'middle',
                    class: 'axis-label',
                }, point.date));
            }
        });
        document.addEventListener('keydown', (event) => {
            if (event.key !== 'Enter' && event.key !== ' ') return;
            const card = event.target.closest('.portfolio-card-clickable');
            if (!card || event.target !== card) return;
            event.preventDefault();
            showPortfolioDetail(Number(card.dataset.id));
        });
    }

    function drawDonutChart(svg, totalElement, legendElement, sectors, total) {
        const radius = 65;
        const circumference = 2 * Math.PI * radius;
        svg.setAttribute('viewBox', '0 0 160 160');
        svg.replaceChildren(svgNode('circle', { cx: 80, cy: 80, r: radius, class: 'donut-ring-bg' }));
        totalElement.textContent = currency(total, true);
        const validSectors = sectors.filter((sector) => Number(sector.value) > 0);
        let offset = 0;
        validSectors.forEach((sector, index) => {
            const length = total > 0 ? Number(sector.value) / total * circumference : 0;
            svg.appendChild(svgNode('circle', {
                cx: 80, cy: 80, r: radius, class: 'donut-segment', stroke: chartColors[index % chartColors.length],
                'stroke-dasharray': `${length} ${circumference - length}`,
                'stroke-dashoffset': -offset,
            }));
            offset += length;
        });
        legendElement.innerHTML = validSectors.slice(0, 6).map((sector, index) => `
            <div class="allocation-item"><i style="background:${chartColors[index % chartColors.length]}"></i><span>${escapeHtml(sector.name)}</span><b>${total ? (Number(sector.value) / total * 100).toFixed(1) : '0.0'}%</b></div>
        `).join('') || '<div class="empty-state">No asset allocation data yet.</div>';
    }

    function drawAllocationChart(sectors, total) {
        drawDonutChart(
            byId('allocation-chart'),
            byId('allocation-total'),
            byId('allocation-legend'),
            sectors,
            total,
        );
    }

    function renderBars(container, rows, labelKey = 'name', valueKey = 'value') {
        const total = rows.reduce((sum, row) => sum + Number(row[valueKey] || 0), 0);
        container.innerHTML = rows.length ? rows.slice(0, 8).map((row, index) => {
            const value = Number(row[valueKey]) || 0;
            const share = total ? value / total * 100 : 0;
            return `<div class="bar-item"><div class="bar-item-top"><span>${escapeHtml(row[labelKey])}</span><span>${currency(value)} · ${share.toFixed(1)}%</span></div><div class="bar-track"><div class="bar-fill ${index ? 'secondary' : ''}" style="width:${Math.max(1, share)}%"></div></div></div>`;
        }).join('') : '<div class="empty-state">No allocation data available.</div>';
    }

    function renderBestPerformers(rows, container, count) {
        const performers = rows.slice(0, count);
        container.innerHTML = performers.length ? performers.map((row) => `
            <div class="performer-row"><div class="performer-name"><strong>${escapeHtml(row.symbol)} · ${escapeHtml(row.security_name)}</strong><small>${escapeHtml(row.sector || 'Unclassified')} · ${Number(row.quantity).toLocaleString('en-IN')} shares</small></div>
                <span class="performer-return ${Number(row.pnl_percentage) >= 0 ? 'positive-text' : 'negative-text'}">${Number(row.pnl_percentage) >= 0 ? '+' : ''}${Number(row.pnl_percentage).toFixed(2)}%</span>
                <span class="performer-value">${signed(row.pnl)}</span></div>
        `).join('') : '<div class="empty-state">No open holdings to compare.</div>';
    }

    function renderAnalytics() {
        const analytics = state.analytics;
        if (!analytics) return;
        drawPortfolioChart(byId('analytics-performance-chart'), analytics.portfolio_performance || []);
        renderBars(byId('analytics-sectors'), analytics.sector_allocation || []);
        renderBars(byId('analytics-stocks'), analytics.stock_allocation || []);
        renderBars(byId('investor-comparison'), (analytics.investor_comparison || []).map((investor) => ({
            name: investor.investor_name,
            value: investor.current_value,
        })));
        renderBestPerformers(analytics.top_performers || [], byId('analytics-best'), 5);
        renderBestPerformers(analytics.worst_performers || [], byId('analytics-worst'), 5);
        renderMonthlyActivity();
        const activity = new Map((analytics.trade_activity || []).map((item) => [item.trade_type, item]));
        byId('trade-activity').innerHTML = ['BUY', 'SELL'].map((type) => {
            const item = activity.get(type) || { trade_count: 0, trade_value: 0 };
            const isBuy = type === 'BUY';
            return `<div class="activity-card ${isBuy ? 'buy' : 'sell'}"><span>${isBuy ? 'BUY ORDERS' : 'SELL ORDERS'}</span><strong>${Number(item.trade_count).toLocaleString('en-IN')}</strong><small>${currency(item.trade_value)} total transaction value</small></div>`;
        }).join('');
        renderRisk(analytics.risk || {});
    }

    function renderRisk(risk) {
        byId('risk-category').textContent = risk.category || 'No positions yet';
        byId('risk-sector').textContent = `${Number(risk.largest_sector_weight || 0).toFixed(1)}%`;
        byId('risk-stock').textContent = `${Number(risk.largest_stock_weight || 0).toFixed(1)}%`;
        byId('risk-counts').textContent = `${Number(risk.sector_count || 0)} / ${Number(risk.stock_count || 0)}`;
        const values = [
            { name: 'Largest sector concentration', value: Number(risk.largest_sector_weight || 0) },
            { name: 'Largest individual stock', value: Number(risk.largest_stock_weight || 0) },
        ];
        byId('risk-breakdown').innerHTML = values.map((item) => `
            <div class="bar-item"><div class="bar-item-top"><span>${item.name}</span><span>${item.value.toFixed(1)}%</span></div>
                <div class="bar-track"><div class="bar-fill ${item.value >= 25 ? 'secondary' : ''}" style="width:${Math.max(0, Math.min(100, item.value))}%"></div></div></div>
        `).join('');
    }

    function openPortfolioModal(portfolio = null) {
        elements.portfolioForm.reset();
        elements.portfolioId.value = portfolio ? portfolio.portfolio_id : '';
        elements.portfolioName.value = portfolio ? portfolio.portfolio_name : '';
        elements.portfolioModalTitle.textContent = portfolio ? 'Edit portfolio' : 'New portfolio';
        elements.savePortfolioButton.textContent = portfolio ? 'Save changes' : 'Create portfolio';
        elements.portfolioInvestorField.hidden = true;
        elements.portfolioInvestor.value = state.selectedInvestorId || '';
        elements.portfolioModal.showModal();
    }

    async function savePortfolio(event) {
        event.preventDefault();
        const id = elements.portfolioId.value;
        const body = { portfolio_name: elements.portfolioName.value.trim() };
        const options = {
            method: id ? 'PUT' : 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ...body, investor_id: Number(state.selectedInvestorId || elements.portfolioInvestor.value) }),
        };
        elements.savePortfolioButton.disabled = true;
        try {
            const result = await api(id ? `/api/portfolios/${id}` : '/api/portfolios', options);
            elements.portfolioModal.close();
            showNotification(result.message);
            await refreshData();
        } catch (error) {
            showNotification(error.message, 'error');
        } finally {
            elements.savePortfolioButton.disabled = false;
        }
    }

    async function deletePortfolio(id) {
        const portfolio = state.portfolios.find((item) => Number(item.portfolio_id) === id);
        if (!portfolio || !window.confirm(`Delete "${portfolio.portfolio_name}"? Positions will be removed. Portfolios with transaction history cannot be deleted.`)) {
            return;
        }
        try {
            const result = await api(`/api/portfolios/${id}`, {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ investor_id: Number(state.selectedInvestorId) }),
            });
            showNotification(result.message);
            await refreshData();
        } catch (error) {
            showNotification(error.message, 'error');
        }
    }

    async function loadSecurityDetail(id) {
        const params = new URLSearchParams({ period: state.securityHistoryPeriod });
        if (state.selectedInvestorId) params.set('investor_id', state.selectedInvestorId);
        const result = await api(`/api/securities/${id}?${params}`);
        const security = result.data;
        state.securityDetailId = Number(security.security_id);
        byId('security-detail-title').textContent = `${security.security_name} · ${security.symbol}`;
        byId('security-detail-subtitle').textContent = `${security.symbol} · ${security.sector || 'Unclassified'} · NSE symbol as stored in SECURITY`;
        byId('security-detail-price').textContent = currency(security.current_price);
        byId('security-detail-portfolios').textContent = Number(security.portfolio_count).toLocaleString('en-IN');
        byId('security-detail-quantity').textContent = Number(security.shares_held).toLocaleString('en-IN');
        byId('security-detail-sector').textContent = security.sector || 'Unclassified sector';
        const securityHoldings = security.holdings || [];
        byId('security-detail-holding-count').textContent = `${securityHoldings.length} ${securityHoldings.length === 1 ? 'portfolio' : 'portfolios'}`;
        byId('security-detail-holdings').innerHTML = securityHoldings.length ? securityHoldings.map((holding) => `
            <tr><td><button class="text-button" data-action="view-portfolio" data-id="${Number(holding.portfolio_id)}">${escapeHtml(holding.portfolio_name)}</button></td>
                <td>${escapeHtml(holding.investor_name)}</td><td class="align-right">${Number(holding.quantity).toLocaleString('en-IN')}</td>
                <td class="align-right">${currency(holding.average_buy_price)}</td><td class="align-right">${currency(holding.current_value)}</td></tr>
        `).join('') : '<tr><td colspan="5" class="empty-cell">No portfolios currently hold this security.</td></tr>';
        const history = security.historical_prices || [];
        const chartAvailable = history.length >= 2;
        byId('security-history-chart').classList.toggle('hidden', !chartAvailable);
        byId('security-history-empty').classList.toggle('hidden', chartAvailable);
        byId('security-history-empty').textContent = security.history_table_available
            ? (security.history_message || 'At least two dated prices are required to draw this chart.')
            : 'PRICE_HISTORY is not installed yet. Apply database/07_price_history.sql, then import genuine CSV closing prices.';
        if (chartAvailable) drawHistoryChart(byId('security-history-chart'), history, 'close_price', 'price_date');
        document.querySelectorAll('[data-security-period]').forEach((button) => {
            button.classList.toggle('active', button.dataset.securityPeriod === state.securityHistoryPeriod);
        });
        const transactions = security.transactions || [];
        byId('security-detail-trade-count').textContent = `${transactions.length} ${transactions.length === 1 ? 'record' : 'records'}`;
        byId('security-detail-trades').innerHTML = transactions.length ? transactions.map((trade) => `
            <tr><td>${Number(trade.trade_id)}</td><td>${escapeHtml(trade.trade_date)}</td><td>${escapeHtml(trade.investor_name)}</td><td>${escapeHtml(trade.portfolio_name)}</td>
                <td><span class="trade-tag ${trade.trade_type === 'BUY' ? 'buy' : 'sell'}">${escapeHtml(trade.trade_type)}</span></td>
                <td class="align-right">${Number(trade.quantity).toLocaleString('en-IN')}</td><td class="align-right">${currency(trade.trade_price)}</td>
                <td>${Number(trade.is_voided) ? `<span class="void-status">${escapeHtml(trade.void_reason || 'Voided')}</span><br><small>${escapeHtml(trade.voided_by || 'Unknown user')} · ${escapeHtml(trade.voided_at || 'Time unavailable')}</small>` : 'Active'}</td></tr>
        `).join('') : '<tr><td colspan="8" class="empty-cell">No transactions are recorded for this security.</td></tr>';
        const watched = state.watchlist.some((item) => Number(item.security_id) === state.securityDetailId);
        elements.securityDetailWatchlist.textContent = watched ? '★ Remove from watchlist' : '☆ Add to watchlist';
    }

    async function showSecurityDetail(id) {
        try {
            state.securityDetailId = Number(id);
            state.securityHistoryPeriod = '1M';
            setPage('security-detail');
            await loadWatchlist();
            await loadSecurityDetail(state.securityDetailId);
        } catch (error) {
            showNotification(error.message, 'error');
        }
    }

    async function loadPortfolioDetail(id) {
        const result = await api(`/api/portfolios/${id}?investor_id=${encodeURIComponent(state.selectedInvestorId)}`);
        const portfolio = result.data;
        state.portfolioDetailId = Number(portfolio.portfolio_id);
        byId('portfolio-detail-title').textContent = portfolio.portfolio_name;
        byId('portfolio-detail-subtitle').textContent = `${portfolio.investor_name} · Created ${portfolio.created_date} · current valuations use SECURITY.current_price`;
        byId('portfolio-detail-value').textContent = currency(portfolio.portfolio_value);
        byId('portfolio-detail-invested').textContent = currency(portfolio.total_invested);
        byId('portfolio-detail-realized').textContent = signed(portfolio.realized_pnl);
        byId('portfolio-detail-unrealized').textContent = signed(portfolio.unrealized_pnl);
        byId('portfolio-detail-total-pnl').textContent = signed(portfolio.total_pnl);
        byId('portfolio-detail-return').textContent = portfolio.return_percentage === null
            ? '—' : `${Number(portfolio.return_percentage) >= 0 ? '+' : ''}${Number(portfolio.return_percentage).toFixed(2)}%`;
        byId('portfolio-detail-xirr').textContent = portfolio.xirr_available
            ? `${Number(portfolio.xirr_percentage) >= 0 ? '+' : ''}${Number(portfolio.xirr_percentage).toFixed(2)}%`
            : 'Unavailable';
        byId('portfolio-detail-xirr-note').textContent = portfolio.xirr_message;
        byId('portfolio-detail-realized').classList.toggle('positive-text', Number(portfolio.realized_pnl) >= 0);
        byId('portfolio-detail-realized').classList.toggle('negative-text', Number(portfolio.realized_pnl) < 0);
        byId('portfolio-detail-unrealized').classList.toggle('positive-text', Number(portfolio.unrealized_pnl) >= 0);
        byId('portfolio-detail-unrealized').classList.toggle('negative-text', Number(portfolio.unrealized_pnl) < 0);
        byId('portfolio-detail-total-pnl').classList.toggle('positive-text', Number(portfolio.total_pnl) >= 0);
        byId('portfolio-detail-total-pnl').classList.toggle('negative-text', Number(portfolio.total_pnl) < 0);
        byId('portfolio-detail-return').classList.toggle('positive-text', Number(portfolio.return_percentage) >= 0);
        byId('portfolio-detail-return').classList.toggle('negative-text', Number(portfolio.return_percentage) < 0);
        const historyAvailable = Boolean(portfolio.historical_performance_available);
        byId('portfolio-history-chart').classList.toggle('hidden', !historyAvailable);
        byId('portfolio-history-empty').classList.toggle('hidden', historyAvailable);
        byId('portfolio-history-empty').textContent = portfolio.historical_performance_message || 'Historical prices are unavailable.';
        if (historyAvailable) drawHistoryChart(byId('portfolio-history-chart'), portfolio.historical_performance, 'value', 'date');
        const allocation = (portfolio.sector_allocation || []).map((row) => ({
            name: row.sector,
            value: row.current_value,
        }));
        drawDonutChart(
            byId('portfolio-detail-allocation-chart'),
            byId('portfolio-detail-allocation-total'),
            byId('portfolio-detail-allocation-legend'),
            allocation,
            Number(portfolio.portfolio_value),
        );
        renderBars(byId('portfolio-detail-sectors'), allocation);

        const holdings = portfolio.holdings || [];
        byId('portfolio-detail-holdings-count').textContent = `${holdings.length} ${holdings.length === 1 ? 'position' : 'positions'}`;
        byId('portfolio-detail-holdings').innerHTML = holdings.length ? holdings.map((holding) => `
            <tr><td>${symbolCell(holding.symbol, holding.security_name)}</td><td>${escapeHtml(holding.sector)}</td>
                <td class="align-right">${Number(holding.quantity).toLocaleString('en-IN')}</td>
                <td class="align-right" title="${escapeHtml(holding.cost_basis_source)}">${currency(holding.invested_value)}</td><td class="align-right">${currency(holding.current_price)}</td>
                <td class="align-right">${currency(holding.current_value)}</td>
                <td class="align-right ${Number(holding.realized_pnl) >= 0 ? 'positive-text' : 'negative-text'}">${signed(holding.realized_pnl)}</td>
                <td class="align-right ${Number(holding.unrealized_pnl) >= 0 ? 'positive-text' : 'negative-text'}">${signed(holding.unrealized_pnl)}</td></tr>
        `).join('') : '<tr><td colspan="8" class="empty-cell">No open holdings in this portfolio.</td></tr>';
        const transactions = portfolio.transactions || [];
        byId('portfolio-detail-trade-count').textContent = `${transactions.length} ${transactions.length === 1 ? 'record' : 'records'}`;
        byId('portfolio-detail-trades').innerHTML = transactions.length ? transactions.map((trade) => `
            <tr><td>${Number(trade.trade_id)}</td><td>${escapeHtml(trade.trade_date)}</td><td>${symbolCell(trade.symbol, trade.security_name)}</td>
                <td><span class="trade-tag ${trade.trade_type === 'BUY' ? 'buy' : 'sell'}">${escapeHtml(trade.trade_type)}</span></td>
                <td class="align-right">${Number(trade.quantity).toLocaleString('en-IN')}</td><td class="align-right">${currency(trade.trade_price)}</td>
                <td class="align-right">${currency(trade.total_trade_amount)}</td>
                <td>${Number(trade.is_voided) ? `<span class="void-status">${escapeHtml(trade.void_reason || 'Voided')}</span><br><small>${escapeHtml(trade.voided_by || 'Unknown user')} · ${escapeHtml(trade.voided_at || 'Time unavailable')}</small>` : 'Active'}</td></tr>
        `).join('') : '<tr><td colspan="8" class="empty-cell">No transactions are recorded for this portfolio.</td></tr>';
    }

    async function showPortfolioDetail(id) {
        if (!state.selectedInvestorId) {
            navigateToPage('portfolio-detail');
            elements.investorFilter.focus();
            return;
        }
        try {
            state.portfolioDetailId = Number(id);
            setPage('portfolio-detail');
            await loadPortfolioDetail(state.portfolioDetailId);
        } catch (error) {
            showNotification(error.message, 'error');
        }
    }

    async function submitTrade(event) {
        event.preventDefault();
        const missing = [
            [elements.formInvestor, 'Select an investor.'],
            [elements.formPortfolio, 'Select a portfolio.'],
            [elements.formSecurity, 'Select a security.'],
            [elements.formDate, 'Select a transaction date.'],
        ].find(([input]) => !input.value);
        if (missing) {
            setTradeFormError(missing[1]);
            missing[0].focus();
            return;
        }
        const quantity = Number(elements.formQuantity.value);
        const price = Number(elements.formPrice.value);
        if (!Number.isSafeInteger(quantity) || quantity <= 0 || !Number.isFinite(price) || price <= 0) {
            setTradeFormError('Enter a whole-share quantity and a price greater than zero.');
            return;
        }
        if (await validateSellCapacity()) return;
        setTradeFormError('');
        const button = byId('btn-submit-trade');
        const body = {
            investor_id: Number(elements.formInvestor.value),
            portfolio_id: Number(elements.formPortfolio.value),
            security_id: Number(elements.formSecurity.value),
            trade_type: document.querySelector('input[name="trade_type"]:checked').value,
            quantity,
            trade_price: price,
            trade_date: elements.formDate.value,
        };
        button.disabled = true;
        button.textContent = 'Saving transaction…';
        try {
            const result = await api('/api/trade', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body),
            });
            showNotification(result.message);
            elements.tradeForm.reset();
            setTradeFormError('');
            elements.formInvestor.value = state.selectedInvestorId;
            elements.formDate.value = localDate();
            await loadFormPortfolios(state.selectedInvestorId);
            elements.tradeEstimate.textContent = currency(0);
            await refreshData();
        } catch (error) {
            showNotification(error.message, 'error');
        } finally {
            button.disabled = false;
            button.textContent = 'Submit transaction';
        }
    }

    function updateTradeEstimate() {
        const total = (Number(elements.formQuantity.value) || 0) * (Number(elements.formPrice.value) || 0);
        elements.tradeEstimate.textContent = currency(total);
    }

    function setTradeFormError(message) {
        elements.tradeFormError.textContent = message;
        elements.tradeFormError.classList.toggle('hidden', !message);
    }

    async function validateSellCapacity() {
        const sequence = ++state.sellCheckSequence;
        const tradeType = document.querySelector('input[name="trade_type"]:checked').value;
        if (tradeType !== 'SELL') {
            setTradeFormError('');
            return false;
        }
        const portfolioId = elements.formPortfolio.value;
        const securityId = elements.formSecurity.value;
        const requested = Number(elements.formQuantity.value);
        if (!portfolioId || !securityId || !Number.isSafeInteger(requested) || requested <= 0) return false;
        try {
            const result = await api(`/api/holdings?investor_id=${encodeURIComponent(state.selectedInvestorId)}&portfolio_id=${encodeURIComponent(portfolioId)}`);
            if (sequence !== state.sellCheckSequence) return false;
            const holding = result.data.find((item) => Number(item.security_id) === Number(securityId));
            const available = Number(holding?.quantity || 0);
            if (requested > available) {
                setTradeFormError(`Insufficient quantity to sell. Available: ${available}; requested: ${requested}.`);
                return true;
            }
            setTradeFormError('');
            return false;
        } catch (error) {
            setTradeFormError(`Could not verify available shares: ${error.message}`);
            return true;
        }
    }

    async function loadFormPortfolios(investorId) {
        elements.formPortfolio.replaceChildren();
        if (!investorId) {
            appendOption(elements.formPortfolio, '', 'Choose investor first');
            elements.formPortfolio.disabled = true;
            return;
        }
        try {
            const result = await api(`/api/portfolios?investor_id=${encodeURIComponent(investorId)}`);
            appendOption(elements.formPortfolio, '', 'Choose portfolio');
            result.data.forEach((portfolio) => {
                appendOption(elements.formPortfolio, portfolio.portfolio_id, portfolio.portfolio_name);
            });
            elements.formPortfolio.disabled = false;
        } catch (error) {
            showNotification(error.message, 'error');
        }
    }

    async function onInvestorChange() {
        state.selectedInvestorId = elements.investorFilter.value;
        const selectedInvestor = state.investors.find((item) => String(item.investor_id) === state.selectedInvestorId);
        byId('user-avatar').textContent = selectedInvestor ? selectedInvestor.investor_name.slice(0, 1).toUpperCase() : 'E';
        state.selectedPortfolioId = '';
        state.watchlist = [];
        state.portfolios = [];
        state.holdings = [];
        state.trades = [];
        state.analytics = null;
        state.investorHoldings = [];
        state.investorTrades = [];
        state.selectedInvestor = selectedInvestor || null;
        state.investorContextLoading = true;
        elements.portfolioFilter.value = '';
        elements.portfolioFilter.disabled = !state.selectedInvestorId;
        if (state.currentPage === 'portfolio-detail') state.portfolioDetailId = null;
        elements.formInvestor.value = state.selectedInvestorId;
        setPage(state.currentPage, false);
        renderSecurities();
        if (state.market) renderMarket();
        if (state.currentPage === 'security-detail') {
            byId('security-detail-portfolios').textContent = '0';
            byId('security-detail-quantity').textContent = '0';
            byId('security-detail-holding-count').textContent = 'Loading investor context…';
            byId('security-detail-holdings').innerHTML = '<tr><td colspan="5" class="empty-cell">Loading selected investor holdings…</td></tr>';
            byId('security-detail-trade-count').textContent = 'Loading…';
            byId('security-detail-trades').innerHTML = '<tr><td colspan="8" class="empty-cell">Loading selected investor activity…</td></tr>';
        }
        try {
            await loadFormPortfolios(state.selectedInvestorId);
            await refreshData();
            await loadWatchlist();
            renderSecurities();
            if (state.market) renderMarket();
            if (state.currentPage === 'security-detail' && state.securityDetailId) {
                await loadSecurityDetail(state.securityDetailId);
            }
            if (state.currentPage === 'portfolio-detail') navigateToPage('portfolios');
            if (state.currentPage === 'investors') await loadInvestors();
        } catch (error) {
            showNotification(error.message, 'error');
        } finally {
            state.investorContextLoading = false;
            setPage(state.currentPage, false);
        }
    }

    document.querySelectorAll('.nav-link').forEach((link) => {
        link.addEventListener('click', () => navigateToPage(link.dataset.page));
    });
    document.addEventListener('click', (event) => {
        if (event.target.closest('[data-select-investor]')) {
            elements.investorFilter.focus();
            return;
        }
        const navigation = event.target.closest('[data-navigate]');
        if (navigation) navigateToPage(navigation.dataset.navigate);
        const openTrade = event.target.closest('[data-open-trade]');
        if (openTrade) {
            navigateToPage('transactions');
            const investorId = openTrade.dataset.investorId || state.selectedInvestorId;
            const portfolioId = openTrade.dataset.portfolioId;
            if (investorId) {
                elements.formInvestor.value = investorId;
                loadFormPortfolios(investorId).then(() => {
                    if (portfolioId) elements.formPortfolio.value = portfolioId;
                    elements.formInvestor.focus();
                });
            } else {
                elements.formInvestor.focus();
            }
            if (openTrade.dataset.action === 'record-portfolio-trade') return;
        }
        const closeModal = event.target.closest('[data-close-modal]');
        if (closeModal) closeModal.closest('dialog').close();
        const action = event.target.closest('[data-action]');
        if (!action) return;
        const id = Number(action.dataset.id);
        if (action.dataset.action === 'edit-portfolio') {
            const portfolio = state.portfolios.find((item) => Number(item.portfolio_id) === id);
            if (portfolio) openPortfolioModal(portfolio);
        } else if (action.dataset.action === 'delete-portfolio') {
            deletePortfolio(id);
        } else if (action.dataset.action === 'view-portfolio') {
            showPortfolioDetail(id);
        } else if (action.dataset.action === 'toggle-watchlist') {
            toggleWatchlist(id);
        } else if (action.dataset.action === 'void-trade') {
            openVoidTradeModal(id);
        } else if (action.dataset.action === 'view-security') {
            showSecurityDetail(id);
        } else if (action.dataset.action === 'save-target') {
            saveTargetPrice(id);
        } else if (action.dataset.action === 'view-investor') {
            elements.investorFilter.value = String(id);
            setPage('investor-workspace');
            onInvestorChange().catch((error) => showNotification(error.message, 'error'));
        }
    });

    byId('add-portfolio-button').addEventListener('click', () => openPortfolioModal());
    elements.portfolioForm.addEventListener('submit', savePortfolio);
    elements.voidTradeForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const reason = elements.voidTradeReason.value.trim();
        const tradeId = Number(elements.voidTradeId.value);
        if (!tradeId || !reason) {
            showNotification('A reason is required before voiding a trade.', 'error');
            return;
        }
        try {
            await voidTrade(tradeId, reason);
            elements.voidTradeModal.close();
            elements.voidTradeForm.reset();
        } catch (error) {
            showNotification(error.message, 'error');
        }
    });
    elements.securityWatchlistButton.addEventListener('click', async () => {
        if (state.securityDetailId) {
            await toggleWatchlist(state.securityDetailId);
            const watched = state.watchlist.some((item) => Number(item.security_id) === state.securityDetailId);
            elements.securityWatchlistButton.textContent = watched ? '★ Remove from watchlist' : '＋ Add to watchlist';
        }
    });
    elements.securityDetailWatchlist.addEventListener('click', async () => {
        if (!state.securityDetailId) return;
        await toggleWatchlist(state.securityDetailId);
        await loadSecurityDetail(state.securityDetailId).catch((error) => showNotification(error.message, 'error'));
    });
    document.querySelectorAll('[data-security-period]').forEach((button) => {
        button.addEventListener('click', () => {
            state.securityHistoryPeriod = button.dataset.securityPeriod;
            if (state.securityDetailId) {
                loadSecurityDetail(state.securityDetailId).catch((error) => showNotification(error.message, 'error'));
            }
        });
    });
    elements.investorFilter.addEventListener('change', onInvestorChange);
    elements.portfolioFilter.addEventListener('change', () => {
        state.selectedPortfolioId = elements.portfolioFilter.value;
        refreshData();
    });
    elements.formInvestor.addEventListener('change', () => {
        setTradeFormError('');
        if (elements.formInvestor.value !== state.selectedInvestorId) {
            elements.investorFilter.value = elements.formInvestor.value;
            onInvestorChange();
            return;
        }
        loadFormPortfolios(elements.formInvestor.value);
    });
    [elements.formPortfolio, elements.formSecurity].forEach((select) => select.addEventListener('change', () => {
        validateSellCapacity();
    }));
    elements.formSecurity.addEventListener('change', () => {
        const security = state.securities.find((item) => String(item.security_id) === elements.formSecurity.value);
        if (security) {
            elements.formPrice.value = Number(security.current_price).toFixed(2);
            updateTradeEstimate();
        }
    });
    [elements.formQuantity, elements.formPrice].forEach((input) => input.addEventListener('input', () => {
        updateTradeEstimate();
        validateSellCapacity();
    }));
    document.querySelectorAll('input[name="trade_type"]').forEach((input) => input.addEventListener('change', validateSellCapacity));
    elements.tradeForm.addEventListener('submit', submitTrade);
    byId('refresh-button').addEventListener('click', async () => {
        elements.statusDot.className = 'status-dot';
        await checkHealth();
        try {
            const securities = await api('/api/securities');
            state.securities = securities.data;
            populateSecurities();
            renderSecurities();
        } catch (error) {
            showNotification(error.message, 'error');
        }
        await refreshData();
        await loadMarket();
        if (state.currentPage === 'watchlist') await loadWatchlist();
        if (state.currentPage === 'investors') await loadInvestors();
        if (elements.statusDot.classList.contains('online')) showNotification('Your portfolio data is up to date.');
    });
    byId('mobile-menu').addEventListener('click', () => elements.sidebar.classList.toggle('open'));
    elements.securitySearch.addEventListener('input', () => {
        window.clearTimeout(securityTimer);
        securityTimer = window.setTimeout(renderSecurities, 120);
    });
    [elements.securitySector, elements.securitySort, elements.securityMinPrice, elements.securityMaxPrice].forEach((input) => {
        input.addEventListener(input === elements.securityMinPrice || input === elements.securityMaxPrice ? 'input' : 'change', renderSecurities);
    });
    const marketInputs = [
        elements.marketSearch, elements.marketSector, elements.marketMinPrice, elements.marketMaxPrice, elements.marketSort,
    ];
    marketInputs.forEach((input) => input.addEventListener(
        input === elements.marketSearch || input === elements.marketMinPrice || input === elements.marketMaxPrice ? 'input' : 'change',
        () => {
            window.clearTimeout(holdingsTimer);
            holdingsTimer = window.setTimeout(() => loadMarket().catch((error) => showNotification(error.message, 'error')), 180);
        },
    ));
    [elements.holdingsSearch, elements.holdingsSector, elements.holdingsSort, elements.holdingsGroupToggle].forEach((input) => {
        input.addEventListener(input === elements.holdingsSearch ? 'input' : 'change', () => {
            window.clearTimeout(holdingsTimer);
            holdingsTimer = window.setTimeout(() => {
                if (input === elements.holdingsGroupToggle || input === elements.holdingsSearch ||
                    input === elements.holdingsSector || input === elements.holdingsSort) {
                    renderHoldings();
                }
            }, 120);
        });
    });
    elements.tradeStatusFilter.addEventListener('change', renderTrades);
    [elements.tradeTypeFilter, elements.tradePortfolioFilter, elements.tradeSecurityFilter, elements.tradeFromDate, elements.tradeToDate].forEach((input) => {
        input.addEventListener('change', () => loadTrades().catch((error) => showNotification(error.message, 'error')));
    });
    elements.tradeSearch.addEventListener('input', () => {
        window.clearTimeout(securityTimer);
        securityTimer = window.setTimeout(() => loadTrades().catch((error) => showNotification(error.message, 'error')), 180);
    });
    elements.investorSearch.addEventListener('input', renderInvestors);
    elements.watchlistSearch.addEventListener('input', renderWatchlist);
    elements.watchlistSector.addEventListener('change', renderWatchlist);
    elements.portfolioSearch.addEventListener('input', renderPortfolios);
    elements.portfolioSort.addEventListener('change', renderPortfolios);
    elements.globalSearch.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' && elements.globalSearch.value.trim()) {
            elements.securitySearch.value = elements.globalSearch.value.trim();
            navigateToPage('securities');
            renderSecurities();
        }
    });
    byId('export-trades').addEventListener('click', () => {
        exportCSV('equitydesk-transactions.csv',
            ['Trade ID', 'Date', 'Investor', 'Portfolio', 'Symbol', 'Company', 'Type', 'Quantity', 'Price', 'Amount'],
            state.trades.map((trade) => [
                trade.trade_id, trade.trade_date, trade.investor_name, trade.portfolio_name,
                trade.symbol, trade.security_name, trade.trade_type, trade.quantity, trade.trade_price, trade.total_trade_amount,
            ]));
    });
    byId('export-holdings').addEventListener('click', () => {
        exportCSV('equitydesk-holdings.csv',
            ['Investor', 'Portfolio', 'Symbol', 'Company', 'Sector', 'Quantity', 'Average buy price', 'Current database price', 'Invested value', 'Current value', 'Unrealized P&L', 'Return %'],
            state.holdings.map((holding) => [
                holding.investor_name, holding.portfolio_name, holding.symbol, holding.security_name, holding.sector,
                holding.quantity, holding.average_buy_price, holding.current_price, holding.invested_value,
                holding.current_value, holding.pnl, holding.pnl_percentage,
            ]));
    });
    byId('export-investor-holdings').addEventListener('click', () => {
        if (!state.selectedInvestor) return;
        exportCSV(`equitydesk-${state.selectedInvestor.investor_name.replace(/[^a-z0-9]+/gi, '-').toLowerCase()}-holdings.csv`,
            ['Portfolio', 'Symbol', 'Company', 'Sector', 'Quantity', 'Average buy price', 'Current database price', 'Invested value', 'Current value', 'Unrealized P&L'],
            state.investorHoldings.map((holding) => [
                holding.portfolio_name, holding.symbol, holding.security_name, holding.sector,
                holding.quantity, holding.average_buy_price, holding.current_price,
                holding.invested_value, holding.current_value, holding.pnl,
            ]));
    });
    [elements.portfolioModal, elements.securityModal].forEach((dialog) => {
        dialog.addEventListener('click', (event) => {
            if (event.target === dialog) dialog.close();
        });
    });
    window.addEventListener('hashchange', () => {
        const page = window.location.hash.slice(1);
        if (pageCopy[page]) navigateToPage(page);
        else if (!page) navigateToPage('market');
    });

    async function start() {
        elements.formDate.value = localDate();
        const initialPage = window.location.hash.slice(1);
        setPage(pageCopy[initialPage] ? initialPage : 'market');
        const results = await Promise.allSettled([
            api('/api/investors'),
            api('/api/securities'),
        ]);
        if (results[0].status === 'fulfilled') {
            state.investors = results[0].value.data;
            populateInvestors();
            renderInvestors();
        } else {
            showNotification(results[0].reason.message, 'error');
        }
        if (results[1].status === 'fulfilled') {
            state.securities = results[1].value.data;
            populateSecurities();
            renderSecurities();
        } else {
            showNotification(results[1].reason.message, 'error');
        }
        await checkHealth();
        await loadMarket();
        if (state.currentPage === 'investors') renderInvestors();
        if (state.currentPage === 'securities') await loadWatchlist();
        if (state.currentPage === 'watchlist') await loadWatchlist();
        if (state.currentPage === 'investor-workspace') await loadInvestorWorkspace();
    }

    start().catch((error) => showNotification(error.message, 'error'));
});
