# **************************************************************************
# *
# * Authors:  Javier Mota Garcia (jmota@cnb.csic.es), February 2018
# *
# * Unidad de  Bioinformatica of Centro Nacional de Biotecnologia , CSIC
# *
# * This program is free software; you can redistribute it and/or modify
# * it under the terms of the GNU General Public License as published by
# * the Free Software Foundation; either version 2 of the License, or
# * (at your option) any later version.
# *
# * This program is distributed in the hope that it will be useful,
# * but WITHOUT ANY WARRANTY; without even the implied warranty of
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# * GNU General Public License for more details.
# *
# * You should have received a copy of the GNU General Public License
# * along with this program; if not, write to the Free Software
# * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA
# * 02111-1307  USA
# *
# *  All comments concerning this program package may be sent to the
# *  e-mail address 'scipion@cnb.csic.es'
# *
# **************************************************************************

from pyworkflow.em import *
import pyworkflow.protocol.constants as pwconst
from prody import *
from pyworkflow.utils import *
import time

FILE = 0
PDB = 1

SCIPION_HOME = os.environ['SCIPION_HOME']

class computePdbTrajectories(EMProtocol):
    """ Protocol to execute functions from ProDy software"""

    _label = "Generate Trajectories ProDy"

    def _defineParams(self, form):
        self.defaultCycles = 5

        form.addSection(label="ProDy Generate Trajectories")
        form.addParam('initialPdb', PointerParam, pointerClass='PdbFile',
                      label='Initial Pdb', important=False,
                      help='Choose an initial conformation using a Pdb to '
                           'compute its N trajectories')
        form.addParam('useFinalPdb', params.BooleanParam, default=False,
                      label="Use final conformation")
        form.addParam('finalPdb', PointerParam, pointerClass='PdbFile',
                      label='Final Pdb', important=True, condition = 'useFinalPdb == True',
                      help='Choose a final conformation using a Pdb to '
                           'compute its N trajectories')
        form.addParam('usingPseudoatoms', params.BooleanParam, default=False,
                      label="Using Pseudoatoms?")
        form.addParam('threshold', params.FloatParam, default = 0.0, label="Threshold",
                      condition="usingPseudoatoms == True",
                      help = "You need to set a threshold to reduce the number of pseudoatoms "
                             "depending on your computer memory. This threshold takes the "
                             "pseudoatoms with maximum intensity. If you get a memory error try to "
                             "increase the threshold")
        form.addParam('cycleNumber', params.IntParam,
                      default=self.defaultCycles,
                      label='Number of cycles',
                      condition = 'useFinalPdb == False',
                      important=True, help='Number of cycles to cover a '
                                           'landscape')
        form.addParam('numTrajectories', params.IntParam, default=1,
                      label='Number of trajectories',
                      important=True, help='Number of trajectories to generate')
        form.addParam('anmCutoff', params.IntParam, default=15,
                      label='ANM Cutoff', expertLevel = pwconst.LEVEL_ADVANCED,
                      help='Maximum distance that two residues are in contact.')
        form.addParam('maxDeviation', params.FloatParam, default=1.5,
                      label='Maximum deviation per normal mode (A)',
                      expertLevel = pwconst.LEVEL_ADVANCED,
                      help='The maximum deviation per step when disturbing the '
                           'protein structure in ANM-MC.')
        form.addParam('acceptanceParam', params.FloatParam, default=0.9,
                      label='Acceptance Ratio', expertLevel =
                      pwconst.LEVEL_ADVANCED, condition = 'useFinalPdb==True',
                      help='The ratio for accepting uphill ANM-MC steps, '
                           'i.e. those that do not approach the target '
                           'structure.')
        form.addParam('maxNumSteps', params.IntParam, default=1000000,
                      label='Max number of ANM steps', expertLevel=
                      pwconst.LEVEL_ADVANCED,
                      help='Maximal number of steps in ANM-MC step.')
        form.addParam('stepCut', params.FloatParam, default=2,
                      label='RMSD cutoff for ANM-MC steps',
                      expertLevel=pwconst.LEVEL_ADVANCED,
                      help='If the total deviation from the starting '
                           'structure exceeds this value, the ANM-MC stepping '
                           'stops.')
        form.addParam('minLen', params.FloatParam, default=1,
                      label='Minimisation length  (ps)',
                      expertLevel=pwconst.LEVEL_ADVANCED,
                      condition='usingPseudoatoms == False',
                      help='This value is given in ps to be comparable to TMD '
                           'length. Each ps is equivalent to 500 steps.')
        form.addParam('tmdLen', params.FloatParam, default=10,
                      label='Targeted MD length (ps)',
                      expertLevel=pwconst.LEVEL_ADVANCED,
                      condition='usingPseudoatoms == False',
                      help='This length depends on the size of the protein '
                           'with bigger proteins needing longer. As an '
                           'indication, 10 ps was used for the leucine '
                           'transporter, which has about 500 residues.')

    def _insertAllSteps(self):
        self._insertFunctionStep('createTrajectories')
        self._insertFunctionStep('createOutputStep')

    def createTrajectories(self):

        self.initialFileName = self.initialPdb.get().getFileName()

        if self.usingPseudoatoms.get() is True:
            usingPseudoatoms = 1
            pseudoatomsFile = open(self.initialFileName,'r')

            for n, line in enumerate(pseudoatomsFile.readlines()):
                self.numPseudoatoms = n
            pseudoatomsFile.close()
            if self.numPseudoatoms > 10000: #Esta condicion es dependiendo de cada ordenador
                pseudoatomsFile = open(self.initialFileName, 'r')
                newFile = self._getExtraPath('pseudoatomsReduced.pdb')
                pseudoatomsReduced = open(newFile, 'w')
                self.numPseudoatoms = 0
                for n, line in enumerate(pseudoatomsFile.readlines()):
                    column = line.split()

                    try:
                        if n >= 3 and n < 10000:
                            intensity = column[9]
                        if n >= 10000:
                            intensity = column[8]

                        if n < 3 or float(intensity) > self.threshold: #0.15
                            self.numPseudoatoms += 1
                            pseudoatomsReduced.write(str(line))
                    except:
                        print "Pseudoatom skipped line %s"%line

                pseudoatomsReduced.close()
                self.initialFileName = newFile
            pseudoatomsFile.close()

        else:
            usingPseudoatoms = 0

        self._params = {'initPdb': self.initialFileName,
                        'numTraj': self.numTrajectories.get(),
                        'cutoff': self.anmCutoff.get(),
                        'maxDev': self.maxDeviation.get(),
                        'acceptParam': self.acceptanceParam.get(),
                        'maxSteps': self.maxNumSteps.get(),
                        # 'spr': self.spring.get(),
                        'cycle': self.cycleNumber.get(),
                        'minLen': self.minLen.get(),
                        'tmdLen': self.tmdLen.get(),
                        'stepCut': self.stepCut.get(),
                        'usingPseudoatoms': usingPseudoatoms
                        }

        if self.useFinalPdb.get() is True:
            self._params['finPdb'] = self.finalPdb.get().getFileName()
            self._params['cycle'] = self.defaultCycles
        else:
            self._params['finPdb'] = self._params['initPdb']

        for traj in range(self.numTrajectories.get()):
            if self.usingPseudoatoms.get() is True:
                self.pseudoatomsTrajectory(traj)
            else:
               self.atomsTrajectory(traj)

            if self.useFinalPdb.get():
                if self.usingPseudoatoms.get() is True:
                    w1_start = parsePDB(str(self._params['initPdb']))
                    w1_traj = parseDCD(self._getExtraPath('initr.dcd'))
                    w1_traj.setCoords(w1_start)
                    w1_traj.setAtoms(w1_start)
                    writeDCD(self._getExtraPath(
                        'walker1_trajectory{:02d}_protein.dcd'.format(
                            traj + 1)), w1_traj)

                    w2_start = parsePDB(str(self._params['finPdb']))
                    w2_traj = parseDCD(self._getExtraPath('initr.dcd'))
                    w2_traj.setCoords(w2_start)
                    w2_traj.setAtoms(w2_start)
                    writeDCD(self._getExtraPath(
                        'walker2_trajectory{:02d}_protein.dcd'.format(
                            traj + 1)),
                        w2_traj)

                    os.system(
                        'mv walker2_trajectory.dcd walker2_trajectory{:02d}'
                        '.dcd'.format(traj + 1))
                else:
                    w1_start = parsePDB(self._getExtraPath(
                        'walker1_ionized.pdb'))
                    w1_traj = parseDCD(self._getExtraPath('walker1_trajectory.dcd'))
                    w1_traj.setCoords(w1_start)
                    w1_traj.setAtoms(w1_start.select('protein and not hydrogen'))
                    writeDCD(self._getExtraPath(
                             'walker1_trajectory{:02d}_protein.dcd'.format(traj+1)),
                             w1_traj)

                    w2_start = parsePDB( self._getExtraPath('walker2_ionized.pdb'))
                    w2_traj = parseDCD( self._getExtraPath('walker2_trajectory.dcd'))
                    w2_traj.setCoords(w2_start)
                    w2_traj.setAtoms(w2_start.select('protein and not hydrogen'))
                    writeDCD(self._getExtraPath(
                             'walker2_trajectory{:02d}_protein.dcd'.format(traj+1)),
                             w2_traj)

                combined_traj = parseDCD(self._getExtraPath(
                                         'walker1_trajectory{:02d}_protein.dcd'
                                         .format(traj+1)))

                for i in reversed(range(len(w2_traj))):
                    combined_traj.addCoordset(w2_traj.getConformation(i))

                writeDCD( self._getExtraPath('trajectory{:02d}.dcd'.format(traj+1)),
                          combined_traj)
                os.system('mv walker2_trajectory.dcd walker2_trajectory{:02d}'
                          '.dcd'.format(traj + 1))
            else:
                if self.usingPseudoatoms.get() is True:
                    w1_start = parsePDB(str(self._params['initPdb']))
                    fnDCD = self._getExtraPath('initr.dcd')
                    if os.path.exists(fnDCD):
                        w1_traj = parseDCD(fnDCD)
                        w1_traj.setCoords(w1_start)
                        w1_traj.setAtoms(w1_start)
                        writeDCD(self._getExtraPath(
                            'trajectory{:02d}.dcd'.format(traj + 1)),
                                 w1_traj)

                else:
                    w1_start = parsePDB(self._getExtraPath(
                        'walker1_ionized.pdb'))
                    fnDCD = self._getExtraPath('walker1_trajectory.dcd')
                    if os.path.exists(fnDCD):
                        w1_traj = parseDCD(fnDCD)
                        w1_traj.setCoords(w1_start)
                        w1_traj.setAtoms(w1_start.select('protein and not hydrogen'))

                        writeDCD(self._getExtraPath('trajectory{:02d}.dcd'.format(traj+1)),
                                w1_traj)

            if self.usingPseudoatoms.get() is False:
                os.system('mv walker1_trajectory.dcd walker1_trajectory{:02d}.dcd'.
                      format(traj+1))

                os.system('mv rmsd.txt trajectory{:02d}_rmsd.txt'.format(traj + 1))

    def atomsTrajectory(self, traj):
        print("Calculating trajectory %d..." % (traj + 1))
        sys.stdout.flush()
        args = ('-args ' + " " + str(os.path.abspath(self._getExtraPath()))
                + " " + "results{0}".format(str(traj + 1))
                + " " + self._params['initPdb']
                + " " + self._params['finPdb']
                + " " + str(self._params['cycle'])
                + " " + str(self._params['maxDev'])
                + " " + str(self._params['acceptParam'])
                + " " + str(self._params['stepCut'])
                + " " + str(self._params['minLen'])
                + " " + str(self._params['tmdLen'])
                + " " + str(self._params['cutoff'])
                + " " + str(self._params['maxSteps'])
                + " & ")

        self.runJob("VMDARGS='text with blanks' vmd -dispdev text -e " +
                    os.path.abspath(os.environ['SCIPION_HOME'] +
                                    '/software/em/prody/vmd-1.9.3/lib/plugins/noarch/tcl'
                                    '/comd/comd.tcl'), args)

        outputFn = self._getExtraPath('results{0}.log'.format(traj + 1))
        finished = 0
        while not finished:
            if exists(outputFn):
                file = open(outputFn, 'r')
                lines = file.readlines()
                for line in lines:

                    if line.find("ERROR") != -1:
                        raise OSError(line)

                    elif line.find("FINISHED") != -1:
                        finished = 1
                        print("Trajectory done.")
                        sys.stdout.flush()

                file.close()


    def pseudoatomsTrajectory(self, traj):

        print("Calculating pseudoatoms trajectory %d..." % (traj + 1))
        finished = False
        i = 0
        while not finished:

            if self.useFinalPdb.get() is True:
                n = 2
            else:
                n = 1

            for sim in range(n):
                if sim == 0:
                    if i == 0:
                        currIniPdb = self._params['initPdb']
                        currFinPdb = self._params['finPdb']

                        IniPdb = parsePDB(currIniPdb)
                        init_traj = Ensemble()
                        init_traj.setCoords(IniPdb)
                        init_traj.setAtoms(IniPdb)
                        init_traj.addCoordset(IniPdb.getCoordsets())
                        writeDCD(self._getExtraPath("initr.dcd"), init_traj)

                    else:
                        currIniDcd = parseDCD(str(self._getExtraPath(
                            'ini_cycle{0}.dcd'.format(i - 1))))
                        initPdb = parsePDB(str(self._params['initPdb']))
                        currIniDcd.setCoords(initPdb)
                        currIniDcd.setAtoms(initPdb)
                        writePDB(str(self._getExtraPath(
                            'ini_cycle{0}.pdb'.format(i - 1))),
                            currIniDcd)
                        currIniPdb = self._getExtraPath(
                            'ini_cycle{0}.pdb'.format(i - 1))

                        if self.useFinalPdb.get() is True:
                            currFinDcd = parseDCD(str(self._getExtraPath(
                                'fin_cycle{0}.dcd'.format(i - 1))))
                            finPdb = parsePDB(str(self._params['finPdb']))
                            currFinDcd.setCoords(finPdb)
                            currFinDcd.setAtoms(finPdb)
                            writePDB(str(self._getExtraPath(
                                'fin_cycle{0}.pdb'.format(i - 1))),
                                currFinDcd)
                            currFinPdb = self._getExtraPath(
                                'fin_cycle{0}.pdb'.format(i - 1))

                    outputDcdName = str(self._getExtraPath(
                        'ini_cycle{0}.dcd'.format(i)))
                else:
                    if i == 0:
                        currIniPdb = self._params['finPdb']
                        currFinPdb = self._params['initPdb']

                        IniPdb2 = parsePDB(currIniPdb)
                        init_traj = Ensemble()
                        init_traj.setCoords(IniPdb2)
                        init_traj.setAtoms(IniPdb2)
                        init_traj.addCoordset(IniPdb2.getCoordsets())
                        writeDCD(self._getExtraPath("fintr.dcd"), init_traj)
                    else:
                        currIniDcd = parseDCD(str(self._getExtraPath(
                            'fin_cycle{0}.dcd'.format(i - 1))))
                        initPdb = parsePDB(str(self._params['finPdb']))
                        currIniDcd.setCoords(initPdb)
                        currIniDcd.setAtoms(initPdb)
                        writePDB(str(self._getExtraPath(
                            'fin_cycle{0}.pdb'.format(i - 1))), currIniDcd)
                        currIniPdb = self._getExtraPath(
                            'fin_cycle{0}.pdb'.format(i - 1))

                        currFinDcd = parseDCD(str(self._getExtraPath(
                            'ini_cycle{0}.dcd'.format(i - 1))))
                        finPdb = parsePDB(str(self._params['initPdb']))
                        currFinDcd.setCoords(finPdb)
                        currFinDcd.setAtoms(finPdb)
                        writePDB(str(self._getExtraPath(
                            'ini_cycle{0}.pdb'.format(i - 1))),
                            currFinDcd)
                        currFinPdb = self._getExtraPath(
                            'ini_cycle{0}.pdb'.format(i - 1))

                    outputDcdName = str(self._getExtraPath(
                        'fin_cycle{0}.dcd'.format(i)))

                args = (currIniPdb
                        + " " + currFinPdb
                        + " " + self._params['initPdb']
                        + " " + self._params['finPdb']
                        + " " + str(i)
                        + " " + str(self._params['maxDev'])
                        + " " + str(self._params['stepCut'])
                        + " " + str(self._params['acceptParam'])
                        + " " + str(self._params['cutoff'])
                        + " " + str(self._params['maxSteps'])
                        + " " + outputDcdName
                        + " " + str(int(self.usingPseudoatoms.get())))

                self.runJob("python " + os.path.abspath(os.environ[
                             'SCIPION_HOME'] + "/software/em/prody/vmd-1.9.3/"
                                               "lib/plugins/noarch/tcl"
                                                          "/comd/anmmc.py"), args)

            os.system("prody catdcd " + str(self._getExtraPath(
                'initr.dcd')) + " " + str(self._getExtraPath(
                'ini_cycle%d.dcd' % i)) + " " + "-o " + str(
                self._getExtraPath("initial.dcd")))
            os.system("mv " + self._getExtraPath('initial.dcd') +
                      " " + self._getExtraPath('initr.dcd'))

            if self.useFinalPdb.get() is True:
                os.system("prody catdcd " + str(self._getExtraPath(
                    'fintr.dcd')) + " " + str(self._getExtraPath(
                    'fin_cycle%d.dcd' % i)) + " " + "-o " + str(
                    self._getExtraPath("final.dcd")))
                os.system("mv " + self._getExtraPath('final.dcd') +
                          " " + self._getExtraPath('fintr.dcd'))

            if self.cycleNumber.get() is not None and \
                    i + 1 >= self.cycleNumber.get():
                finished = True
            i += 1


    def createOutputStep(self):
        print("Starting createOutputStep")
        sys.stdout.flush()

        setOfPDBs = self._createSetOfPDBs()
        setOfTrajectories = self._createSetOfTrajectories()
        for n in range(self.numTrajectories.get()):
            try:
                fnDcd = self._getExtraPath('trajectory{:02d}.dcd'.format(n+1))
                ens = parseDCD(fnDcd)
                if self.usingPseudoatoms.get() is True:
                    protein = parsePDB(str(self._params['initPdb']))
                else:
                    atoms = parsePDB(self._getExtraPath('walker1_ionized.pdb'))
                    protein = atoms.select('protein and not hydrogen').copy()
                ens.setCoords(protein)
                ens.setAtoms(protein)
                fnPdb = []
                for i, conformation in enumerate(ens):
                    fnPdb.append(self._getExtraPath('trajectory{:02d}_pdb{:02d}.pdb'.format(n + 1,i + 1)))
                    writePDB(fnPdb[i], conformation)
                    pdb = PdbFile(fnPdb[i],self.usingPseudoatoms.get(), self.initialPdb.get().getDeviation())
                    setOfPDBs.append(pdb)
                traj = TrajectoryDcd(fnDcd,
                       self._getExtraPath('trajectory{:02d}_pdb01.pdb'.format(n+1)), self.usingPseudoatoms.get(),
                                     self.initialPdb.get().getDeviation())
                setOfTrajectories.append(traj)
            except:
                pass

        self._defineOutputs(outputPDBs=setOfPDBs)
        self._defineSourceRelation(self.initialPdb.get(), setOfPDBs)

        self._defineOutputs(outputTrajs=setOfTrajectories)
        self._defineSourceRelation(self.initialPdb.get(), setOfTrajectories)

        print("Finished createOutputStep")
        sys.stdout.flush()

    def _summary(self):
        summary = []
        try:
            summary.append("Number of pseudoatoms: %d"% self.numPseudoatoms)
        except:
            summary.append("Number of pseudoatoms not ready yet")

        return summary










