// Location: frontend/lib/constants.ts
export const EXPERIMENT_OPTIONS = [
    { value: "AutoTSF_ETTh1", label: "Time Series Forecasting (ETTh1)" },
    { value: "AutoCls3D_ModelNet40", label: "3D Classification (ModelNet40)" },
    { value: "AutoSeg_VOC12", label: "Semantic Segmentation (VOC12)" },
    { value: "AutoPCDet_Once", label: "3D Object Detection (Once)" },
    { value: "sentiment_classification_sst2", label: "Sentiment Classification (SST-2)" },
    { value: "AutoEAP_UMI-STARR-seq", label: "Enhancer Activity Prediction" },
    { value: "AutoTPPR_Perturb-seq", label: "Perturbation Response Prediction" },
    { value: "AutoMolecule3D_MD17", label: "Molecular Dynamics (MD17)" },
    { value: "AutoPower_IEEE39_bus", label: "Power System (IEEE39 Bus)" },
];

export const MODEL_OPTIONS = [
    { value: "gemini-2.5-flash-lite", label: "Gemini 2.5 Flash Lite" },
    { value: "gpt-4o", label: "GPT-4o" },
    { value: "claude-3-sonnet", label: "Claude 3 Sonnet" },
];

export const CODE_MODEL_OPTIONS = [
    { value: "flash", label: "Gemini 2.5 Flash" },
    { value: "gpt-4o", label: "GPT-4o" },
    { value: "claude-3-sonnet",label: "Claude 3 Sonnet" },
    { value: "deepseek-r1", label: "DeepSeek R1" }
];