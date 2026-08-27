import { useEffect, useState } from 'react';
import { Link, Navigate, NavLink, Route, Routes, useLocation, useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { deleteAdminArtwork, downloadOriginal, getAdminArtworks, getAdminUsers, getGallery, getMyArtworks, getMyPurchases, getRecommendations, login, purchaseArtwork, register, requestPasswordReset, resetPassword, updateAdminUser, uploadArtwork, verifyOwnership } from './api';
import { connectWallet, contractAddress, digitalArtAbi } from './contract';

const sampleArtworks = [
  { id: 'demo-1', title: 'Tidal Memory', artist_id: 'Aster Vale', ipfs_cid: '', price: '0.18 ETH', verified: true, owner: '0x8d...42a1' },
  { id: 'demo-2', title: 'Soft Machinery', artist_id: 'Niko Sato', ipfs_cid: '', price: '0.24 ETH', verified: true, owner: '0x12...c0de' },
  { id: 'demo-3', title: 'Quiet Orbit', artist_id: 'Mara Lin', ipfs_cid: '', price: '0.31 ETH', verified: true, owner: '0x73...91b4' },
];

function RequireAuth({ user, children }) {
  const location = useLocation();
  if (user) return children;
  return <Navigate to="/login" replace state={{ from: location.pathname }} />;
}

function RequireRole({ user, roles, children }) {
  if (!user) return <Navigate to="/login" replace />;
  return roles.includes(user.role) ? children : <Navigate to="/dashboard" replace />;
}

function Layout({ user, onLogout, onLogin }) {
  return <div className="app-shell">
    <header className="topbar">
      <Link className="brand" to={user ? '/dashboard' : '/gallery'}><span className="brand-mark">D</span><span>Digital Art<br /><strong>Protection</strong></span></Link>
      <nav className="main-nav">
        {user?.role === 'artist' && <><NavLink to="/dashboard">Dashboard</NavLink><NavLink to="/upload">Upload artwork</NavLink><NavLink to="/my-artworks">My work</NavLink></>}
        {user?.role === 'buyer' && <><NavLink to="/dashboard">Dashboard</NavLink><NavLink to="/gallery">Gallery</NavLink><NavLink to="/verify">Verify</NavLink><NavLink to="/my-purchases">My purchases</NavLink></>}
        {!user && <NavLink to="/gallery">Gallery</NavLink>}
        {user?.role === 'admin' && <NavLink to="/admin">Admin</NavLink>}
        {user && <NavLink to="/profile">Profile</NavLink>}
      </nav>
      <div className="account-actions">{user ? <><span className="user-chip">{user.username}</span><button className="button button-quiet" onClick={onLogout}>Sign out</button></> : <Link className="button button-dark" to="/login">Enter studio</Link>}</div>
    </header>
    <main className="content"><Routes>
      <Route path="/" element={<Navigate to={user ? '/dashboard' : '/login'} replace />} />
      <Route path="/gallery" element={<RequireRole user={user} roles={['buyer']}><Gallery /></RequireRole>} />
      <Route path="/dashboard" element={<RequireAuth user={user}><Dashboard user={user} /></RequireAuth>} />
      <Route path="/login" element={<Auth mode="login" onLogin={onLogin} />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      <Route path="/reset-password" element={<ResetPassword />} />
      <Route path="/signup" element={<SignupChoice />} />
      <Route path="/signup/artist" element={<Auth mode="artist-signup" />} />
      <Route path="/signup/buyer" element={<Auth mode="buyer-signup" />} />
      <Route path="/upload" element={<RequireRole user={user} roles={['artist']}><Upload /></RequireRole>} />
      <Route path="/verify" element={<RequireRole user={user} roles={['buyer']}><Verify /></RequireRole>} />
      <Route path="/my-artworks" element={<RequireRole user={user} roles={['artist']}><MyArtworks /></RequireRole>} />
      <Route path="/my-purchases" element={<RequireRole user={user} roles={['buyer']}><MyPurchases /></RequireRole>} />
      <Route path="/purchase/:id" element={<RequireRole user={user} roles={['buyer']}><Purchase /></RequireRole>} />
      <Route path="/recommendations" element={<RequireRole user={user} roles={['buyer']}><Recommendations /></RequireRole>} />
      <Route path="/profile" element={<RequireAuth user={user}><Profile user={user} /></RequireAuth>} />
      <Route path="/admin" element={<RequireRole user={user} roles={['admin']}><Admin /></RequireRole>} />
    </Routes></main>
    <footer><span>Human-made work deserves a permanent record.</span><span>Local network ready · Hardhat · IPFS · Ethereum</span></footer>
  </div>;
}

function Gallery() {
  const [artworks, setArtworks] = useState(sampleArtworks);
  const [status, setStatus] = useState('');
  useEffect(() => { getGallery().then(setArtworks).catch(() => setStatus('Showing the studio preview. Connect the API to load the live gallery.')); }, []);
  return <section><div className="hero-row"><div><p className="eyebrow">VERIFIED COLLECTION / 2026</p><h1>Art with<br /><em>receipts.</em></h1><p className="lede">A living gallery for human-created digital work, protected by invisible provenance and public ownership records.</p></div><div className="hero-stat"><strong>{String(artworks.length).padStart(2, '0')}</strong><span>verified pieces<br />in view</span></div></div>{status && <div className="notice">{status}</div>}<div className="section-heading"><h2>Latest verified work</h2><Link to="/recommendations">Explore by similarity →</Link></div><div className="art-grid">{artworks.map((artwork, index) => <ArtworkCard key={artwork.id} artwork={artwork} index={index} showPurchase />)}</div></section>;
}

function SignupChoice() {
  return <section className="narrow-page auth-choice"><p className="eyebrow">JOIN THE STUDIO</p><h1>Choose your<br /><em>starting point.</em></h1><p className="lede">Create an account for the work you make or the work you collect. Your account type determines the tools you can access.</p><div className="choice-grid"><Link className="choice-card" to="/signup/artist"><strong>Artist</strong><span>Protect and register original work.</span><b>→</b></Link><Link className="choice-card" to="/signup/buyer"><strong>Buyer</strong><span>Discover, verify, and collect artwork.</span><b>→</b></Link></div></section>;
}

function Dashboard({ user }) {
  const artist = user.role === 'artist';
  return <section className="dashboard-page"><p className="eyebrow">{artist ? 'ARTIST WORKSPACE' : 'COLLECTOR WORKSPACE'}</p><h1>Good to see you,<br /><em>{user.username}.</em></h1><p className="lede">{artist ? 'Build a trusted public record for every human-made piece.' : 'Find verified work and keep your collection in one place.'}</p><div className="dashboard-grid">{artist ? <><Link className="dashboard-card dashboard-card-primary" to="/upload"><small>01 / CREATE</small><strong>Upload artwork</strong><span>Run the human check and register a new piece →</span></Link><Link className="dashboard-card" to="/my-artworks"><small>02 / RECORD</small><strong>My uploaded artworks</strong><span>Review your protected work →</span></Link></> : <><Link className="dashboard-card dashboard-card-primary" to="/gallery"><small>01 / DISCOVER</small><strong>Browse gallery</strong><span>Explore watermarked verified work →</span></Link><Link className="dashboard-card" to="/my-purchases"><small>02 / COLLECTION</small><strong>My purchases</strong><span>Access purchased originals →</span></Link></>}</div></section>;
}

function MyPurchases() { const [artworks, setArtworks] = useState([]); useEffect(() => { getMyPurchases().then(setArtworks).catch(() => setArtworks([])); }, []); return <section><p className="eyebrow">YOUR COLLECTION</p><h1>My<br /><em>purchases.</em></h1>{artworks.length ? <div className="art-grid">{artworks.map((artwork, index) => <ArtworkCard key={artwork.id} artwork={artwork} index={index} />)}</div> : <div className="empty-state"><strong>Your collection is empty.</strong><p>Purchase verified work from the gallery to see it here.</p><Link className="button button-dark" to="/gallery">Browse gallery →</Link></div>}</section>; }

function Profile({ user }) { return <section className="narrow-page profile-page"><p className="eyebrow">ACCOUNT / PROFILE</p><h1>Your<br /><em>record.</em></h1><div className="profile-card"><span className="profile-avatar">{user.username?.slice(0, 1).toUpperCase()}</span><div><h2>{user.username}</h2><p>{user.email}</p><small>Account type: {user.role}</small></div></div></section>; }

function ArtworkCard({ artwork, index, showPurchase = false }) {
  const [previewOpen, setPreviewOpen] = useState(false);
  useEffect(() => {
    if (!previewOpen) return undefined;
    function closeOnEscape(event) {
      if (event.key === 'Escape') setPreviewOpen(false);
    }
    document.addEventListener('keydown', closeOnEscape);
    return () => document.removeEventListener('keydown', closeOnEscape);
  }, [previewOpen]);

  return <><article className={`art-card art-tone-${index % 3}`}><button className="art-image art-image-button" type="button" onClick={() => setPreviewOpen(true)} aria-label={`Open ${artwork.title || 'artwork'} preview`}>{artwork.ipfs_url ? <img src={artwork.ipfs_url} alt={artwork.title || 'Verified digital artwork'} /> : <span className="art-glyph">{['◒', '◈', '⌁'][index % 3]}</span>}<span className="verified-tag">Human verified</span></button><div className="art-meta"><div><h3>{artwork.title || 'Untitled study'}</h3><p>by {artwork.artist_id || 'Unknown artist'}</p><small>On-chain artwork ID: {artwork.blockchain_artwork_id ?? 'pending'}</small></div>{showPurchase && <Link className="purchase-link" to={`/purchase/${artwork.blockchain_artwork_id ?? artwork.id}`}>Purchase</Link>}</div><div className="art-footer"><span>{artwork.price || 'Price on request'}</span><span>{artwork.owner || 'Unclaimed'}</span></div></article>{previewOpen && <div className="art-preview-backdrop" role="presentation" onClick={() => setPreviewOpen(false)}><div className="art-preview" role="dialog" aria-modal="true" aria-label={`${artwork.title || 'Artwork'} preview`} onClick={event => event.stopPropagation()}><button className="art-preview-close" type="button" onClick={() => setPreviewOpen(false)} aria-label="Close artwork preview" title="Close artwork preview"><CloseIcon /></button>{artwork.ipfs_url ? <img src={artwork.ipfs_url} alt={artwork.title || 'Verified digital artwork'} /> : <span className="art-glyph">{['◒', '◈', '⌁'][index % 3]}</span>}<div className="art-preview-caption"><strong>{artwork.title || 'Untitled study'}</strong><span>by {artwork.artist_id || 'Unknown artist'}</span></div></div></div>}</>;
}

function CloseIcon() { return <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 5l14 14M19 5L5 19" /></svg>; }

function Auth({ mode, onLogin }) {
  const navigate = useNavigate();
  const location = useLocation();
  const [form, setForm] = useState({ username: '', email: '', password: '' });
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const isLogin = mode === 'login';
  const role = mode === 'buyer-signup' ? 'buyer' : 'artist';
  async function submit(event) { event.preventDefault(); setError(''); try { if (isLogin) { const user = await login(form); onLogin(user); navigate(location.state?.from || '/dashboard', { replace: true }); } else { await register({ ...form, role }); navigate('/login'); } } catch (err) { setError(err.response?.data?.error || 'The studio is offline. Start the Flask API and try again.'); } }
  return <section className="auth-layout"><div className="auth-copy"><p className="eyebrow">ARTIST ACCESS / SECURE STUDIO</p><h1>{isLogin ? <>Return to<br /><em>your work.</em></> : <>Make a<br /><em>record.</em></>}</h1><p className="lede">Every accepted piece carries a quiet signature and an ownership trail that can be verified anywhere.</p><div className="auth-proof"><span className="proof-mark">D</span><span><strong>One trusted workspace</strong><small>Verify, protect, and transfer original work.</small></span></div></div><form className="form-panel" onSubmit={submit}><div className="form-heading"><span className="form-index">01</span><span>{isLogin ? 'Private artist access' : 'Start your artist record'}</span></div><h2>{isLogin ? 'Sign in' : 'Create your studio account'}</h2>{!isLogin && <label>Artist name<input required value={form.username} onChange={e => setForm({ ...form, username: e.target.value })} /></label>}<label>Email<input required type="email" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} /></label><label>Password<div className="password-field"><input required type={showPassword ? 'text' : 'password'} minLength="8" value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} /><button className="password-toggle" type="button" onClick={() => setShowPassword(!showPassword)} aria-label={showPassword ? 'Hide password' : 'Show password'} title={showPassword ? 'Hide password' : 'Show password'}><EyeIcon visible={showPassword} /></button></div></label>{error && <p className="error">{error}</p>}<button className="button button-dark" type="submit">{isLogin ? 'Enter studio' : 'Create account'} <span>→</span></button><p className="form-switch">{isLogin ? <><Link to="/forgot-password">Forgot password?</Link><br />New here? <Link to="/signup">Create an account</Link></> : <>Already registered? <Link to="/login">Sign in</Link></>}</p></form></section>;
}

function EyeIcon({ visible }) { return visible ? <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 3l18 18M10.6 10.6a2 2 0 0 0 2.8 2.8M9.9 5.2A10.8 10.8 0 0 1 12 5c5.4 0 9 7 9 7a16.5 16.5 0 0 1-3.1 3.8M6.1 6.1C3.8 7.8 3 12 3 12s3.6 7 9 7c1.1 0 2.1-.2 3-.5" /></svg> : <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M2.5 12s3.6-7 9.5-7 9.5 7 9.5 7-3.6 7-9.5 7-9.5-7-9.5-7Z" /><circle cx="12" cy="12" r="2.5" /></svg>; }

function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmation, setConfirmation] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  async function submit(event) {
    event.preventDefault();
    setError('');
    setMessage('');
    if (password !== confirmation) {
      setError('Passwords do not match.');
      return;
    }
    try {
      const response = await requestPasswordReset(email);
      if (response.reset_token) {
        await resetPassword(response.reset_token, password);
        setMessage('Your password has been reset successfully. You can now sign in.');
      } else {
        setMessage(response.message || 'Check your email for password reset instructions.');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Password reset is unavailable.');
    }
  }

  return <section className="auth-layout"><div className="auth-copy"><p className="eyebrow">ACCOUNT RECOVERY / SECURE STUDIO</p><h1>Find your<br /><em>way back.</em></h1><p className="lede">Enter your email and choose a new password for your studio account.</p><div className="auth-proof"><span className="proof-mark">D</span><span><strong>Your work stays protected</strong><small>Reset links expire after 30 minutes.</small></span></div></div><form className="form-panel" onSubmit={submit}><div className="form-heading"><span className="form-index">01</span><span>Recover private access</span></div><h2>Forgot password?</h2><label>Email<input required type="email" value={email} onChange={e => setEmail(e.target.value)} /></label><label>New password<div className="password-field"><input required minLength="8" type={showPassword ? 'text' : 'password'} value={password} onChange={e => setPassword(e.target.value)} /><button className="password-toggle" type="button" onClick={() => setShowPassword(!showPassword)} aria-label={showPassword ? 'Hide new password' : 'Show new password'} title={showPassword ? 'Hide password' : 'Show password'}><EyeIcon visible={showPassword} /></button></div></label><label>Confirm password<div className="password-field"><input required minLength="8" type={showConfirmation ? 'text' : 'password'} value={confirmation} onChange={e => setConfirmation(e.target.value)} /><button className="password-toggle" type="button" onClick={() => setShowConfirmation(!showConfirmation)} aria-label={showConfirmation ? 'Hide confirmation password' : 'Show confirmation password'} title={showConfirmation ? 'Hide password' : 'Show password'}><EyeIcon visible={showConfirmation} /></button></div></label>{error && <p className="error">{error}</p>}{message && <div className="notice">{message}</div>}{!message && <button className="button button-dark" type="submit">Reset password <span>→</span></button>}<p className="form-switch"><Link to="/login">Return to sign in</Link></p></form></section>;
}

function ResetPassword() { const [params] = useSearchParams(); const [password, setPassword] = useState(''); const [showPassword, setShowPassword] = useState(false); const [message, setMessage] = useState(''); const [error, setError] = useState(''); async function submit(event) { event.preventDefault(); setError(''); try { const response = await resetPassword(params.get('token') || '', password); setMessage(response.message); } catch (err) { setError(err.response?.data?.error || 'This reset link is invalid or expired.'); } } return <section className="narrow-page auth-page"><p className="eyebrow">SECURE ACCOUNT RECOVERY</p><h1>Choose a new<br /><em>password.</em></h1><form className="form-panel" onSubmit={submit}><label>New password<div className="password-field"><input required minLength="8" type={showPassword ? 'text' : 'password'} value={password} onChange={e => setPassword(e.target.value)} /><button className="password-toggle" type="button" onClick={() => setShowPassword(!showPassword)} aria-label={showPassword ? 'Hide password' : 'Show password'} title={showPassword ? 'Hide password' : 'Show password'}><EyeIcon visible={showPassword} /></button></div></label>{error && <p className="error">{error}</p>}{message && <div className="notice">{message}</div>}{!message && <button className="button button-dark" type="submit">Save new password <span>→</span></button>}<p className="form-switch"><Link to="/login">Return to sign in</Link></p></form></section>; }

function Upload() {
  const [file, setFile] = useState(null); const [title, setTitle] = useState(''); const [price, setPrice] = useState('0'); const [progress, setProgress] = useState(0); const [result, setResult] = useState(''); const [artworkId, setArtworkId] = useState(null); const [checking, setChecking] = useState(false); const [elapsed, setElapsed] = useState(0); const [classification, setClassification] = useState('');
  useEffect(() => { if (!checking) return undefined; const started = Date.now(); const timer = setInterval(() => setElapsed((Date.now() - started) / 1000), 100); return () => clearInterval(timer); }, [checking]);
  async function submit(event) { event.preventDefault(); if (!file) return setResult('Choose an image first.'); const data = new FormData(); data.append('image', file); data.append('title', title); data.append('price', price); setChecking(true); setProgress(0); setElapsed(0); setResult(''); setArtworkId(null); setClassification(''); try { const response = await uploadArtwork(data, event => setProgress(Math.round((event.loaded * 100) / (event.total || 1)))); setClassification(response.classification || 'Human'); setArtworkId(response.blockchain_artwork_id); setResult(response.message || 'Human work accepted and registered.'); } catch (err) { const responseMessage = err.response?.data?.message || err.response?.data?.error; setClassification(err.response?.status === 422 ? 'AI' : ''); setResult(err.response?.status === 401 ? 'Your session expired. Please sign in again.' : err.response?.status === 422 ? responseMessage || 'This image was rejected by the AI detector.' : responseMessage || 'The upload pipeline is unavailable.'); } finally { setChecking(false); } }
  return <section className="narrow-page upload-page"><div className="upload-intro"><p className="eyebrow">NEW WORK / HUMAN CHECK</p><h1>Put it<br /><em>on record.</em></h1><p className="lede">A rapid AI screening protects the collection before watermarking, IPFS storage, and blockchain registration begin.</p><div className="detection-steps"><span><b>01</b> AI screen</span><span><b>02</b> Protect</span><span><b>03</b> Register</span></div></div><form className="upload-panel" onSubmit={submit}><label className="drop-zone"><input type="file" accept="image/png,image/jpeg,image/webp" onChange={e => { setFile(e.target.files?.[0]); setResult(''); setClassification(''); }} /><span className="upload-plus">+</span><strong>{file ? file.name : 'Choose a digital artwork'}</strong><small>PNG, JPG, or WEBP · up to 25 MB</small></label><label>Title<input value={title} onChange={e => setTitle(e.target.value)} placeholder="Name this piece" /></label><label>Price in ETH<input type="number" min="0" step="0.001" value={price} onChange={e => setPrice(e.target.value)} /></label>{checking && <div className="detection-status"><span className="status-pulse" /><strong>Scanning image and checking provenance</strong><small>{elapsed.toFixed(1)}s · {progress ? `${progress}% uploaded` : 'Preparing rapid analysis'}</small></div>}{progress > 0 && <div className="progress"><span style={{ width: `${progress}%` }} /></div>}<button className="button button-dark" type="submit" disabled={checking}>{checking ? 'Checking artwork...' : 'Run human check'} <span>→</span></button>{result && <div className={`detection-result ${classification === 'Human' ? 'detection-human' : classification === 'AI' ? 'detection-ai' : ''}`}><strong>{classification === 'Human' ? 'Human-generated artwork accepted' : classification === 'AI' ? 'AI-generated artwork rejected' : 'Upload issue'}</strong><span>{result}</span>{artworkId !== null && <small>On-chain artwork ID: <b>{artworkId}</b>. Use this ID on the Verify page.</small>}</div>}</form></section>;
}

function Verify() {
  const [id, setId] = useState(''); const [result, setResult] = useState(null); const [error, setError] = useState('');
  async function submit(event) { event.preventDefault(); setError(''); try { setResult(await verifyOwnership({ artwork_id: id })); } catch (err) { setError(err.response?.data?.error || 'Verification service is unavailable.'); } }
  return <section className="narrow-page"><p className="eyebrow">PROVENANCE CHECK</p><h1>Ask the<br /><em>chain.</em></h1><p className="lede">Confirm the artist, watermark, and current owner for any registered piece.</p><form className="inline-form" onSubmit={submit}><input required value={id} onChange={e => setId(e.target.value)} placeholder="Artwork ID" /><button className="button button-dark">Verify →</button></form>{error && <p className="error">{error}</p>}{result && <div className="result-panel"><span className={result.verified ? 'status-good' : 'status-muted'}>{result.verified ? 'Verified ownership' : 'Not verified'}</span><pre>{JSON.stringify(result, null, 2)}</pre></div>}</section>;
}

function MyArtworks() { const [artworks, setArtworks] = useState([]); useEffect(() => { getMyArtworks().then(setArtworks).catch(() => setArtworks([])); }, []); return <section><p className="eyebrow">YOUR STUDIO</p><h1>My<br /><em>artworks.</em></h1>{artworks.length ? <div className="art-grid">{artworks.map((artwork, index) => <ArtworkCard key={artwork.id} artwork={artwork} index={index} />)}</div> : <div className="empty-state"><strong>No registered pieces yet.</strong><p>Upload your first human-verified artwork to begin your ownership record.</p><Link className="button button-dark" to="/upload">Upload artwork →</Link></div>}</section>; }

function Purchase() { const { id } = useParams(); return <PurchaseInner id={id} />; }
function PurchaseInner({ id }) { const [wallet, setWallet] = useState(''); const [purchased, setPurchased] = useState(false); const [message, setMessage] = useState(''); const [loading, setLoading] = useState(false); const [artwork, setArtwork] = useState(null); useEffect(() => { if (!/^[0-9]+$/.test(String(id))) return; getGallery().then(artworks => setArtwork(artworks.find(item => String(item.blockchain_artwork_id) === String(id)) || null)).catch(() => setArtwork(null)); }, [id]); async function buy() { setLoading(true); setMessage(''); try { if (!/^[0-9]+$/.test(String(id))) { setMessage('This is not a valid blockchain artwork ID. Use the numeric ID shown after upload.'); return; } const { address, web3 } = await connectWallet(); setWallet(address); if (!contractAddress) { setMessage('Wallet connected. Add VITE_CONTRACT_ADDRESS to enable purchase.'); return; } const contract = new web3.eth.Contract(digitalArtAbi, contractAddress); const nextArtworkId = await contract.methods.nextArtworkId().call(); if (BigInt(id) >= BigInt(nextArtworkId)) { setMessage('Artwork ID not found on the current blockchain. Check the ID or redeploy the matching contract.'); return; } const details = await contract.methods.getOwnership(id).call(); if (details.isSold) { setPurchased(true); setMessage('This artwork has already been purchased.'); return; } const tx = await contract.methods.transferOwnership(details.perceptualHash, address).send({ from: address, value: details.price }); await purchaseArtwork({ artwork_id: id, transaction_hash: tx.transactionHash, buyer_address: address }); setPurchased(true); setMessage('Purchase confirmed on Ganache. Your clean original is ready.'); } catch (error) { const errorMessage = error.message || ''; setMessage(errorMessage.includes('Artwork does not exist') || errorMessage.includes('-32603') || errorMessage.includes('execution reverted') ? 'Artwork ID was not found on the current blockchain. Check the numeric ID and contract network.' : errorMessage.includes('Artwork is already sold') ? 'This artwork has already been purchased.' : errorMessage || 'Purchase could not be completed.'); } finally { setLoading(false); } } async function download() { try { const blob = await downloadOriginal(id); const url = URL.createObjectURL(blob); const link = document.createElement('a'); link.href = url; link.download = `artwork-${id}.png`; document.body.appendChild(link); link.click(); link.remove(); URL.revokeObjectURL(url); } catch (error) { setMessage(error.response?.data?.error || 'The clean original could not be downloaded.'); } } return <section className="purchase-layout"><div className="purchase-art art-tone-1">{artwork?.ipfs_url ? <img src={artwork.ipfs_url} alt={artwork.title || `Artwork ${id}`} /> : <span className="art-glyph">◈</span>}<span className="verified-tag">{artwork ? 'Human verified' : 'Artwork preview'}</span></div><div><p className="eyebrow">OWNERSHIP TRANSFER</p><h1>Take it<br /><em>home.</em></h1><p className="lede">Purchase transfers the public ownership record and unlocks the un-watermarked original.</p><div className="purchase-box"><span>{artwork?.title || 'Artwork'}</span><strong>{id}</strong><button className="button button-dark" onClick={buy} disabled={loading || purchased}>{loading ? 'Waiting for Ganache...' : purchased ? 'Already purchased' : wallet ? 'Confirm purchase →' : 'Connect wallet →'}</button>{wallet && <small>{wallet}</small>}{purchased && <button className="button button-outline" onClick={download}>Download clean original ↓</button>}{message && <div className="notice">{message}</div>}</div></div></section>; }

function Recommendations() { const [artworks, setArtworks] = useState([]); const [hash, setHash] = useState(''); const [message, setMessage] = useState(''); async function submit(event) { event.preventDefault(); try { setArtworks(await getRecommendations({ hash })); setMessage(''); } catch (error) { setMessage(error.response?.data?.error || 'Enter a valid pHash.'); } } return <section className="narrow-page"><p className="eyebrow">DISCOVERY / P-HASH</p><h1>Find your<br /><em>next signal.</em></h1><p className="lede">Compare a known pHash against verified work and rank the closest visual matches.</p><form className="inline-form" onSubmit={submit}><input required value={hash} onChange={e => setHash(e.target.value)} placeholder="64-bit pHash, for example ffffffffffffffff" /><button className="button button-dark">Find matches →</button></form>{message && <p className="error">{message}</p>}{artworks.length ? <div className="art-grid">{artworks.map((artwork, index) => <ArtworkCard key={artwork.id} artwork={artwork} index={index} />)}</div> : <div className="empty-state"><strong>No recommendations yet.</strong><p>Enter a stored pHash to find nearby verified pieces.</p></div>}</section>; }

function Admin() { const [users, setUsers] = useState([]); const [artworks, setArtworks] = useState([]); const [message, setMessage] = useState(''); useEffect(() => { Promise.all([getAdminUsers(), getAdminArtworks()]).then(([loadedUsers, loadedArtworks]) => { setUsers(loadedUsers); setArtworks(loadedArtworks); }).catch(error => setMessage(error.response?.data?.error || 'Admin access required.')); }, []); async function toggle(user) { await updateAdminUser(user.id, { disabled: !user.disabled }); setUsers(users.map(item => item.id === user.id ? { ...item, disabled: !item.disabled } : item)); } async function removeArtwork(id) { await deleteAdminArtwork(id); setArtworks(artworks.filter(item => item.id !== id)); setMessage('Artwork removed.'); } return <section className="narrow-page"><p className="eyebrow">ADMINISTRATION</p><h1>Keep the<br /><em>record clean.</em></h1>{message && <div className="notice">{message}</div>}<div className="admin-list"><h2>Users</h2>{users.map(user => <div className="admin-row" key={user.id}><span><strong>{user.username}</strong><small>{user.email}</small></span><button className="button button-outline" onClick={() => toggle(user)}>{user.disabled ? 'Enable' : 'Disable'}</button></div>)}</div><div className="admin-list"><h2>Artwork records</h2>{artworks.map(artwork => <div className="admin-row" key={artwork.id}><span><strong>{artwork.title || 'Untitled'}</strong><small>{artwork.ai_classification} · {artwork.verified ? 'verified' : 'pending'}</small></span><button className="button button-outline" onClick={() => removeArtwork(artwork.id)}>Remove</button></div>)}</div></section>; }

export default function App() { const [user, setUser] = useState(() => JSON.parse(localStorage.getItem('dap_user') || 'null')); function logout() { localStorage.removeItem('dap_user'); localStorage.removeItem('dap_access_token'); setUser(null); } return <Layout user={user} onLogin={setUser} onLogout={logout} />; }
