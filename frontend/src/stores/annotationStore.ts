import { create } from 'zustand'
import type { Study, Series, Image, ROI, AnnotationProject } from '../types'

interface AnnotationState {
  currentStudy: Study | null
  currentSeries: Series | null
  currentImage: Image | null
  currentProject: AnnotationProject | null
  rois: ROI[]
  
  setCurrentStudy: (study: Study | null) => void
  setCurrentSeries: (series: Series | null) => void
  setCurrentImage: (image: Image | null) => void
  setCurrentProject: (project: AnnotationProject | null) => void
  setRois: (rois: ROI[]) => void
  addRoi: (roi: ROI) => void
  updateRoi: (id: string, data: Partial<ROI>) => void
  removeRoi: (id: string) => void
  clearAnnotation: () => void
}

export const useAnnotationStore = create<AnnotationState>((set) => ({
  currentStudy: null,
  currentSeries: null,
  currentImage: null,
  currentProject: null,
  rois: [],
  
  setCurrentStudy: (study) => set({ currentStudy: study, currentSeries: null, currentImage: null }),
  setCurrentSeries: (series) => set({ currentSeries: series }),
  setCurrentImage: (image) => set({ currentImage: image }),
  setCurrentProject: (project) => set({ currentProject: project }),
  setRois: (rois) => set({ rois }),
  addRoi: (roi) => set((state) => ({ rois: [...state.rois, roi] })),
  updateRoi: (id, data) => set((state) => ({
    rois: state.rois.map((r) => (r.id === id ? { ...r, ...data } : r)),
  })),
  removeRoi: (id) => set((state) => ({
    rois: state.rois.filter((r) => r.id !== id),
  })),
  clearAnnotation: () => set({
    currentStudy: null,
    currentSeries: null,
    currentImage: null,
    currentProject: null,
    rois: [],
  }),
}))