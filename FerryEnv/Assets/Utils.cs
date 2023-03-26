using System;
using System.CodeDom;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;
using UnityEngine;

namespace Env
{
    public static class Utils
    {
        public static T[] DecodeMessage<T>(NumpyArray msg)
        {
            var dtype = msg.Dtype;
            var shape = msg.Shape;
            
            // Example dtype: int32, float32, float64
            var dtypeSizeStr = new String(dtype.Where(Char.IsDigit).ToArray());
            var dtypeSize = Int32.Parse(dtypeSizeStr) / 8;
            var output = new T[msg.Data.Length / dtypeSize];
            
            var byteArray = msg.Data.ToByteArray();
            
            Debug.Log($"msg.Data length: {msg.Data.Length}");
            Debug.Log($"data length: {byteArray.Length}");
            Debug.Log($"dtypeSize: {dtypeSize}");
            Debug.Log($"output length: {output.Length}");

            Buffer.BlockCopy(byteArray, 0, output, 0, byteArray.Length);
            
            return output;
        }

        // public static int[] DecodeMessage(NumpyArray msg)
        // {
        //     
        // }
    }

    // public class Decoder
    // {
    //     public static void Decode<T>(byte[] data, out T[] output)
    //     {
    //         decoder.DoDecode(data, out output);
    //     }
    //
    //     private static dynamic decoder = new Decoder();
    //     
    //     private void DoDecode<T>(byte[] data, out T[] output)
    //     {
    //         output = new T[data.Length / 4];
    //     }
    //     
    //     private void DoDecode(byte[] data, out int[] output)
    //     {
    //         output = new int[data.Length / 4];
    //         
    //         Buffer.BlockCopy(data, 0, output, 0, data.Length);
    //     }
    //     
    //     private void DoDecode(byte[] data, out float[] output)
    //     {
    //         output = new float[data.Length / 4];
    //         Buffer.BlockCopy(data, 0, output, 0, data.Length);
    //
    //     }
    //     
    //     private void DoDecode(byte[] data, out double[] output)
    //     {
    //         output = new double[data.Length / 8];
    //     }
    //     
    //     private void DoDecode(byte[] data, out long[] output)
    //     {
    //         output = new long[data.Length / 8];
    //     }
    //     
    //     
    // }
    
}