/***************************************************************************
 *
 * Authors:    Carlos Oscar Sanchez Sorzano coss@cnb.csic.es
 *
 * Unidad de  Bioinformatica of Centro Nacional de Biotecnologia , CSIC
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA
 * 02111-1307  USA
 *
 *  All comments concerning this program package may be sent to the
 *  e-mail address 'xmipp@cnb.csic.es'
 ***************************************************************************/

#ifndef _PROG_CLASSIFICATION_FIRST_SPLIT
#define _PROG_CLASSIFICATION_FIRST_SPLIT

#include <data/xmipp_program.h>

/**@defgroup ClassificationFirstSplit Classification first split
   @ingroup ReconsLibrary */
//@{
/** Classification First Split Parameters. */
class ProgClassifyFirstSplit: public XmippProgram
{
public:
    /** Directional classes */
    FileName fnClasses;
    /** Rootname */
    FileName fnRoot;
    /** Number of reconstructions */
    int Nrec;
    /** Number of samples per reconstruction */
    int Nsamples;
    /** Symmetry */
    FileName fnSym;
public:
    /// Read argument from command line
    void readParams();

    /// Show
    void show();

    /// Define parameters
    void defineParams();

    /// Run
    void run();
};
//@}
#endif
