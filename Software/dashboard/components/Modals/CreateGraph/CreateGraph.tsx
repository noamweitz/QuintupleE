// import React, { useState } from 'react'
// import { XMarkIcon } from '@heroicons/react/24/outline';
// import { getTick } from '@/app/actions';
// import { AllVars } from '@/helpers/graph_data'

// export default function CreateGraph({setPlotGraphModal, addGraph} : any){
//     const [opt, setOpt] = useState<string | undefined>(undefined)

//     const handleClose = ()=>{
//         setPlotGraphModal(false);
//     }

//     const handleMainChange = ({target}: {target: any})=>{
//         setOpt(target.value)
//     } 

//     const handleCreatePlot = async (e: any)=>{
//         if(opt != undefined){
//             const sel = AllVars.find((variable)=>variable.value === opt)
//             if (sel != undefined){
//                 var data = await getTick(sel)
//                 addGraph(data, opt)
//                 handleClose()
//             } else {
//                 console.error("Option selected not found")
//             }
//         } else{
//             console.error("No value selected")
//         }
//     }

//     return (
//         <div className='text-black bg-background flex flex-col text-center w-[50%] max-w-[800px] min-h-[500px] h-[40%] rounded-2xl p-12 animate-ttb-fast'>
//             <div className='flex flex-row justify-end'>
//                 <button onClick={handleClose} className='hover:opacity-50 duration-[0.15s]'>
//                     <XMarkIcon className='size-7'></XMarkIcon>
//                 </button>
//             </div>
//             <h2 className='text-4xl font-bold'>Plot A Graph</h2>
//             <div className='flex flex-col justify-center items-center w-full h-full'>
//                 <select className='w-[300px] mt-auto p-2.5 text-xl text-center rounded-xl shadow-md border-[#001E1D] border-[2px] outline-none' name="" id="" defaultValue="default" onChange={handleMainChange}>
//                     <option value="default" disabled>Select a Variable</option>
//                     {AllVars.map((variable)=><option key={variable.name} value={variable.value}>{variable.name} ({variable.units})</option>)}
//                 </select>
//                 <button 
//                 className='bg-[#001E1D] mt-auto text-white text-xl p-2.5 w-[130px] rounded-xl hover:opacity-75 duration-[0.25s]'
//                 onClick={handleCreatePlot}
//                 >
//                     Plot
//                 </button>
//             </div>
//         </div>
//     );
// }