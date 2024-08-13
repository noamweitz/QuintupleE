import React from 'react';
import { FormatString } from '@/helpers/graph_types';

export default function Connect({data}: any) {
    return (
        <div className='text-primary flex flex-row items-center justify-center flex-nowrap p-10'>
            <div className={(Date.now() - data.lastHeard > 5000? "bg-red-600"	: "bg-green-600") + " w-5 h-5 flex rounded-full m-2 mp-4"}></div>
            <p className='text-xl flex'>{FormatString(data.name)}</p>
        </div>
    );
}