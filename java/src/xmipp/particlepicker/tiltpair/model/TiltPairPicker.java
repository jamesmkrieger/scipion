package xmipp.particlepicker.tiltpair.model;

import java.awt.Color;
import java.io.File;
import java.util.ArrayList;
import java.util.List;
import java.util.logging.Level;

import xmipp.particlepicker.Family;
import xmipp.particlepicker.Format;
import xmipp.particlepicker.Micrograph;
import xmipp.particlepicker.ParticlePicker;
import xmipp.particlepicker.training.model.FamilyState;
import xmipp.particlepicker.training.model.MicrographFamilyData;
import xmipp.particlepicker.training.model.TrainingMicrograph;
import xmipp.utils.XmippMessage;
import xmipp.jni.Filename;
import xmipp.jni.MDLabel;
import xmipp.jni.MetaData;
import java.util.Hashtable;

public class TiltPairPicker extends ParticlePicker {

	protected List<UntiltedMicrograph> micrographs;
	private UntiltedMicrograph micrograph;

	public TiltPairPicker(String selfile, String outputdir, FamilyState state) {
		super(selfile, outputdir, state);
		this.micrographs = new ArrayList<UntiltedMicrograph>();
		loadData();
	}

	private void loadData() {
		try {
			MetaData md = new MetaData(selfile);
			// md.readPlain(pairsfile, "image tilted_image");
			micrographs.clear();
			UntiltedMicrograph untiltedmicrograph;
			TiltedMicrograph tiltedmicrograph;
			String image, tiltedimage;

			long[] ids = md.findObjects();
			for (long id : ids) {
				image = md.getValueString(MDLabel.MDL_MICROGRAPH, id);
				tiltedimage = md.getValueString(MDLabel.MDL_MICROGRAPH_TILTED, id);
				tiltedmicrograph = new TiltedMicrograph(tiltedimage);
				untiltedmicrograph = new UntiltedMicrograph(image, tiltedmicrograph);
				tiltedmicrograph.setUntiltedMicrograph(untiltedmicrograph);
				micrographs.add(untiltedmicrograph);
				loadMicrographParticles(untiltedmicrograph);
			}
			if (micrographs.size() == 0) throw new IllegalArgumentException(String.format("No micrographs specified on %s", selfile));

		} catch (Exception e) {
			getLogger().log(Level.SEVERE, e.getMessage(), e);
			throw new IllegalArgumentException(e);
		}

	}

	public void loadMicrographParticles(UntiltedMicrograph micrograph) {
		String ufile = getOutputPath(micrograph.getPosFile());
		String tfile = getOutputPath(micrograph.getTiltedMicrograph().getPosFile());
		if (Filename.exists(ufile) && Filename.exists(tfile)) loadMicrographData(micrograph, ufile, tfile);
	}

	/* Return number of particles loaded */
	public int loadMicrographParticles(UntiltedMicrograph um, MetaData uMd, MetaData tMd) {
		um.reset();
		UntiltedParticle up;
		TiltedParticle tp;
		TiltedMicrograph tm = um.getTiltedMicrograph();
		int x, y;
		long[] uIds = uMd.findObjects();
		long[] tIds = tMd.findObjects();
		long id;
		int particles = 0;

		for (int i = 0; i < uIds.length; ++i) {
			// Add untilted particle
			id = uIds[i];
			x = uMd.getValueInt(MDLabel.MDL_XCOOR, id);
			y = uMd.getValueInt(MDLabel.MDL_YCOOR, id);
			up = new UntiltedParticle(x, y, um, family);
			um.addParticle(up);
			// Set tilted pair particle
			id = tIds[i];
			x = tMd.getValueInt(MDLabel.MDL_XCOOR, id);
			y = tMd.getValueInt(MDLabel.MDL_YCOOR, id);
			tp = new TiltedParticle(x, y, up);
			up.setTiltedParticle(tp);
			tm.addParticle(tp);
			++particles;
		}

		um.initAligner();

		return particles;
	}// loadMicrographs

	public void loadMicrographData(UntiltedMicrograph um, String uPosFile, String tPosFile) {
		try {
			loadMicrographParticles(um, new MetaData(uPosFile), new MetaData(tPosFile));
		} catch (Exception e) {
			getLogger().log(Level.SEVERE, e.getMessage(), e);
			throw new IllegalArgumentException(e.getMessage());
		}
	}

	public int getNextFreeMicrograph() {
		int count = 0;
		for (UntiltedMicrograph m : micrographs) {
			if (m.hasData()) return count;
			count++;
		}
		return -1;
	}

	public List<UntiltedMicrograph> getMicrographs() {
		return micrographs;
	}

	public void resetMicrograph(UntiltedMicrograph m) {
		m.reset();
		setChanged(true);
	}

	public void resetAllMicrographs() {
		for (UntiltedMicrograph um : micrographs)
			um.reset();
		setChanged(true);
	}

	public int getUntiltedNumber() {
		int count = 0;
		for (UntiltedMicrograph um : micrographs)
			count += um.getParticles().size();
		return count;
	}

	public int getTiltedNumber() {
		int count = 0;
		for (UntiltedMicrograph um : micrographs)
			count += um.getTiltedMicrograph().getParticles().size();
		return count;
	}

	public void saveData() {
		super.saveData();
		long id;

		try {
			MetaData  anglesmd;
			anglesmd = new MetaData(selfile);

			Hashtable<String, Long> micrographsDict = new Hashtable<String, Long>();
			for (long mid : anglesmd.findObjects())
				micrographsDict.put(anglesmd.getValueString(MDLabel.MDL_MICROGRAPH, mid), mid);

			for (UntiltedMicrograph m : micrographs) {
				if (m.hasData()) {

					id = micrographsDict.get(m.getFile());
					anglesmd.setValueDouble(MDLabel.MDL_ANGLE_Y, (double) m.getUntiltedAngle(), id);
					anglesmd.setValueDouble(MDLabel.MDL_ANGLE_Y2, (double) m.getTiltedAngle(), id);
					anglesmd.setValueDouble(MDLabel.MDL_ANGLE_TILT, (double) m.getTiltAngle(), id);

					anglesmd.write(selfile);
				}
				saveData(m);

			}

		} catch (Exception e) {
			getLogger().log(Level.SEVERE, e.getMessage(), e);
			throw new IllegalArgumentException(e.getMessage());
		}

	}

	@Override
	public void saveData(Micrograph m) {
		UntiltedMicrograph um = (UntiltedMicrograph) m;
		String file = getOutputPath(um.getPosFile());
		long id;

		try {
			MetaData md, md2;
			TiltedParticle tp;

			if (!m.hasData())
				new File(file).delete();
			else {

				md = new MetaData();
				md2 = new MetaData();

				for (UntiltedParticle p : um.getParticles()) {
					tp = p.getTiltedParticle();
					if (tp != null) {
						id = md.addObject();
						md.setValueInt(MDLabel.MDL_XCOOR, p.getX(), id);
						md.setValueInt(MDLabel.MDL_YCOOR, p.getY(), id);

						id = md2.addObject();
						md2.setValueInt(MDLabel.MDL_XCOOR, tp.getX(), id);
						md2.setValueInt(MDLabel.MDL_YCOOR, tp.getY(), id);
					}
				}
				String template = family.getName() + "@%s";
				md.write(String.format(template, file));
				md2.write(String.format(template, getOutputPath(um.getTiltedMicrograph().getPosFile())));
			}

		} catch (Exception e) {
			getLogger().log(Level.SEVERE, e.getMessage(), e);
			throw new IllegalArgumentException(e.getMessage());
		}

	}

	@Override
	public int getManualParticlesNumber(Family f) {
		int count = 0;
		for (UntiltedMicrograph um : micrographs)
			count += um.getParticles().size();
		return count;
	}

	@Override
	public void exportParticles(String path) {
		throw new UnsupportedOperationException();

	}// function exportParticles

	@Override
	public Format detectFormat(String path) {
		Format[] formats = { Format.Xmipp24, Format.Xmipp30, Format.Eman };

		for (UntiltedMicrograph um : micrographs) {
			for (Format f : formats)
				if (Filename.exists(getImportMicrographName(path, um.getFile(), f))) return f;
		}
		return Format.Unknown;
	}// function detectFormat

	@Override
	public int importParticlesFromFolder(String path, Format f, float scale, boolean invertx, boolean inverty) {
		if (f == Format.Auto) f = detectFormat(path);
		if (f == Format.Unknown) return 0;

		String uFn, tFn;
		int particles = 0;

		for (UntiltedMicrograph um : micrographs) {
			uFn = getImportMicrographName(path, um.getFile(), f);
			tFn = getImportMicrographName(path, um.getTiltedMicrograph().getFile(), f);
			if (Filename.exists(uFn) && Filename.exists(tFn)) particles += importParticlesFromFiles(uFn, tFn, f, um, scale, invertx, inverty);
		}

		return particles;
	}// function importParticlesFromFolder

	public int importParticlesFromFiles(String uPath, String tPath, Format f, UntiltedMicrograph um, float scale, boolean invertx, boolean inverty) {
		MetaData uMd = new MetaData();
		fillParticlesMdFromFile(uPath, f, um, uMd, scale, invertx, inverty);
		MetaData tMd = new MetaData();
		fillParticlesMdFromFile(tPath, f, um.getTiltedMicrograph(), tMd, scale, invertx, inverty);

		int particles = loadMicrographParticles(um, uMd, tMd);
		uMd.destroy();
		tMd.destroy();
		return particles;
	}// function importParticlesFromFiles
	
	public String getImportMicrographName(String path, String filename, Format f) {
		String base = Filename.removeExtension(Filename.getBaseName(filename));
		switch (f) {
		case Xmipp24:
			return Filename.join(path, base, base + ".raw.Common.pos");
		case Xmipp30:
			return Filename.join(path, base + ".pos");
		case Eman:
			return Filename.join(path, base + "_ptcls.box");

		default:
			return null;
		}
	}
	
	public UntiltedMicrograph getMicrograph()
	{
		return micrograph;
	}

	@Override
	public void setMicrograph(Micrograph m) {
		this.micrograph = (UntiltedMicrograph)m;
		
	}
	


}// class TiltPairPicker
