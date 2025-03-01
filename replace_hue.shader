// Replace Hue 
// Replaces a specific hue in the source with an RGB color
// Smoothly transition from one color to another
// obs-shaderfilter plugin 5/2024

// parameters exposed to OBS

uniform float Tolerance<
    string label = "Tolerance";
    string widget_type = "slider";
    float minimum = 0.0;
    float maximum = 1.0;
    float step = 0.01;
> = 0.05; //<Range(0.0,1.0)>

uniform float Alpha_Percentage<
    string label = "Amount";
    string widget_type = "slider";
    float minimum = 0.0;
    float maximum = 100.0;
    float step = 0.1;
> = 100.0; //<Range(0.0,100.0)>

uniform float target_hue<
    string label = "Target Hue";
    string widget_type = "slider";
    float minimum = 0.0;
    float maximum = 359.9;
    float step = 0.1;
> = 0.0; //<Range(0.0,359.9)>

uniform float from_red<
    string label = "From Red";
    string widget_type = "slider";
    float minimum = 0.0;
    float maximum = 1.0;
    float step = 0.001;
> = 1.0; //<Range(0.0,1.0)>

uniform float from_green<
    string label = "From Green";
    string widget_type = "slider";
    float minimum = 0.0;
    float maximum = 1.0;
    float step = 0.001;
> = 1.0; //<Range(0.0,1.0)>

uniform float from_blue<
    string label = "From Blue";
    string widget_type = "slider";
    float minimum = 0.0;
    float maximum = 1.0;
    float step = 0.001;
> = 1.0; //<Range(0.0,1.0)>

uniform float to_red<
    string label = "To Red";
    string widget_type = "slider";
    float minimum = 0.0;
    float maximum = 1.0;
    float step = 0.001;
> = 1.0; //<Range(0.0,1.0)>

uniform float to_green<
    string label = "To Green";
    string widget_type = "slider";
    float minimum = 0.0;
    float maximum = 1.0;
    float step = 0.001;
> = 1.0; //<Range(0.0,1.0)>

uniform float to_blue<
    string label = "To Blue";
    string widget_type = "slider";
    float minimum = 0.0;
    float maximum = 1.0;
    float step = 0.001;
> = 1.0; //<Range(0.0,1.0)>

uniform float start_time<
    string label = "Start Time";
    string widget_type = "info";
    float minimum = 0.0;
    float maximum = 2147483648.0;
    float step = 0.00001;
> = 0.0; //<Range(0.0,1.0)>

uniform float timestamp<
    string label = "Timestamp";
    string widget_type = "info";
    float minimum = 0.0;
    float maximum = 2147483648.0;
    float step = 0.00001;
> = 0.0; //<Range(0.0,1.0)>

uniform float duration<
    string label = "Duration";
    string widget_type = "slider";
    float minimum = 0.0;
    float maximum = 600.0;
    float step = 0.1;
> = 1.5; //<Range(0.0,600.0)>

uniform float grayscale<
    string label = "GRAYSCALE";
    string widget_type = "slider";
    float minimum = 0.0;
    float maximum = 1.0;
    float step = 1.0;
> = 0.0;


uniform string Notes<
    string widget_type = "info";
> = "Shader to replace one hue with another";

// RGB to HSV conversion methods
// http://chilliant.blogspot.com/2010/11/rgbhsv-in-hlsl.html

float3 Hue(float H)
{
    float R = abs(H * 6 - 3) - 1;
    float G = 2 - abs(H * 6 - 2);
    float B = 2 - abs(H * 6 - 4);
    return saturate(float3(R,G,B));
}

float3 HSVtoRGB(float H, float S, float V)
{
    return ((Hue(H) - 1) * S + 1) * V;
}

float3 RGBtoHSV(in float3 RGB)
{
    float3 HSV = 0;

    HSV.z = max(RGB.r, max(RGB.g, RGB.b));
    float M = min(RGB.r, min(RGB.g, RGB.b));
    float C = HSV.z - M;

    if (C != 0)
    {
        HSV.y = C / HSV.z;
        float3 Delta = (HSV.z - RGB) / C;
        Delta.rgb -= Delta.brg;
        Delta.rg += float2(2,4);
        if (RGB.r >= HSV.z)
            HSV.x = Delta.b;
        else if (RGB.g >= HSV.z)
            HSV.x = Delta.r;
        else
            HSV.x = Delta.g;
        HSV.x = frac(HSV.x / 6);
    }
    return HSV;
}

// method to compare hue values
bool hue_equal(float hue, float target, float t)
{
    float diff = abs(hue - target);
    if (diff > 0.5) diff = 1.0 - diff;
    return diff <= t;
}

float4 mainImage(VertData v_in) : TARGET
{
    float4 original_color = image.Sample(textureSampler, v_in.uv);
    float3 currentHSL = RGBtoHSV(original_color.rgb);

    float4 color;

    float trans_time = clamp((local_time-start_time)/duration, 0.0, 1.0);

    if( hue_equal(currentHSL.x, target_hue/360.0, Tolerance) )
    {
       float3 c = lerp( float3(from_red,from_green,from_blue), float3(to_red,to_green,to_blue), trans_time);
       color = float4(HSVtoRGB(0.0,0.0,currentHSL.z),original_color.a) * float4(c,1.0);
    }
    else if( grayscale && !hue_equal(currentHSL.x, 0.0/360.0, 0.02) )
    {
       color = float4(HSVtoRGB(0.0,0.0,currentHSL.z),original_color.a);
    }
    else
    {
       color = original_color;
    }
    
    return lerp(original_color, color, clamp(Alpha_Percentage * .01, 0, 1.0));

    //float t = (local_time % 5.0) / 5.0;
    //return float4(t,t,t,1);
}
